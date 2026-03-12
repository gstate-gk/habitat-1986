"""
Habitat Web Server.
Converted from: habitat.pl1 (2,379 lines) + regionproc.pl1 (5,455 lines)

Original PL/I server architecture:
    - habitat.pl1: Main process, message coordination
    - regionproc.pl1: Region processing, event loop (s$task_wait_event)
    - hatchery.pl1: Avatar/object creation
    - messages.pl1: Message encoding/routing (n_msg, b_msg, p_msg, e_msg, r_msg)

Python equivalent: FastAPI + WebSocket + asyncio
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path

from .database import init_db, get_region, get_region_objects, save_avatar, load_avatar
from .models import Avatar, ClassID
from .region_processor import RegionProcessor
from .objects import register_all


# --- Global state (PL/I: external declarations) ---
regions: dict[int, RegionProcessor] = {}


async def load_region(region_id: int) -> RegionProcessor | None:
    """Load region from DB and create processor.
    PL/I: s$keyed_read(region_port, 'ident', ...) in habitat_db.pl1"""
    if region_id in regions:
        return regions[region_id]

    region_data = await get_region(region_id)
    if not region_data:
        return None

    processor = RegionProcessor(region_data)
    objects = await get_region_objects(region_id)
    for obj in objects:
        processor.add_object(obj)

    regions[region_id] = processor
    return processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from .seed_data import seed
    await seed()
    register_all()
    yield


app = FastAPI(title="Habitat (1986 Lucasfilm MMO)", lifespan=lifespan)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"


@app.get("/")
async def serve_root():
    index = frontend_path / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"error": "frontend not built"}, status_code=404)


@app.get("/api/regions")
async def list_regions():
    from .database import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT region_id, name FROM regions ORDER BY region_id") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


@app.get("/api/regions/{region_id}")
async def get_region_info(region_id: int):
    proc = await load_region(region_id)
    if not proc:
        return JSONResponse({"error": "region not found"}, status_code=404)
    return proc.get_state()


@app.websocket("/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, player_name: str):
    """Main WebSocket endpoint — replaces PL/I message loop.

    Original PL/I flow:
        1. Client connects → hatchery.pl1: initiate_avatar_creation
        2. Server sends region state → messages.pl1: p_msg_N
        3. Client sends actions → regionproc.pl1: handle_msg
        4. Server broadcasts results → messages.pl1: b_msg_N / e_msg_N
    """
    await websocket.accept()

    # Load or create avatar (PL/I: hatchery.pl1)
    loaded = await load_avatar(player_name)
    if loaded:
        avatar, region_id = loaded
    else:
        avatar = Avatar(name=player_name)
        region_id = 1  # Start in Town Square

    # Enter region
    region = await load_region(region_id)
    if not region:
        await websocket.close(code=1011, reason="region not found")
        return

    avatar_noid = region.add_avatar(avatar, websocket)

    # Send initial state to new player
    await websocket.send_json({
        "type": "INIT",
        "your_noid": avatar_noid,
        "avatar": {
            "noid": avatar_noid,
            "name": avatar.name,
            "x": avatar.x, "y": avatar.y,
            "health": avatar.health,
            "tokens": avatar.tokens_in_hand,
            "bank_account": avatar.bank_account,
        },
        **region.get_state(),
    })

    # Notify others (PL/I: b_msg_N for avatar entry)
    await region.broadcast(avatar_noid, {
        "type": "AVATAR_ENTER",
        "noid": avatar_noid,
        "name": avatar.name,
        "x": avatar.x, "y": avatar.y,
        "activity": avatar.activity,
    })

    try:
        while True:
            msg = await websocket.receive_json()
            result = await region.handle_message(avatar_noid, msg)

            # Handle region change (door/teleport)
            if result.get("_region_change"):
                dest_id = result["destination"]
                new_region = await load_region(dest_id)
                if new_region:
                    # Leave current region
                    await region.broadcast(avatar_noid, {
                        "type": "AVATAR_LEAVE",
                        "noid": avatar_noid,
                        "name": avatar.name,
                    })
                    region.remove_avatar(avatar_noid)
                    await save_avatar(avatar, dest_id)

                    # Enter new region
                    avatar.x = 80
                    avatar.y = 130
                    avatar.travel += 1
                    avatar_noid = new_region.add_avatar(avatar, websocket)
                    region = new_region

                    await websocket.send_json({
                        "type": "REGION_CHANGE",
                        "your_noid": avatar_noid,
                        "avatar": {
                            "noid": avatar_noid, "name": avatar.name,
                            "x": avatar.x, "y": avatar.y,
                            "health": avatar.health,
                            "tokens": avatar.tokens_in_hand,
                            "bank_account": avatar.bank_account,
                        },
                        **new_region.get_state(),
                    })
                    await new_region.broadcast(avatar_noid, {
                        "type": "AVATAR_ENTER",
                        "noid": avatar_noid,
                        "name": avatar.name,
                        "x": avatar.x, "y": avatar.y,
                    })
                    continue

            # Send result to requester
            await websocket.send_json({"type": "ACTION_RESULT", **result})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for {player_name}: {e}")
    finally:
        # Cleanup (PL/I: avatar departure)
        await region.broadcast(avatar_noid, {
            "type": "AVATAR_LEAVE",
            "noid": avatar_noid,
            "name": avatar.name,
        })
        region.remove_avatar(avatar_noid)
        await save_avatar(avatar, region.region.region_id)


# Static files mount MUST be last (catch-all for frontend assets)
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path)), name="frontend")
