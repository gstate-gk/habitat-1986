"""
Database layer.
Converted from: habitat_db.pl1 (1,426 lines)

Original PL/I used Stratus VOS keyed/indexed files:
    s$open(region_port, seq_org, region_size, ...);
    s$keyed_read(region_port, 'ident', '', region_size, ...);

Python equivalent: aiosqlite with async operations.
"""
from __future__ import annotations
import json
import aiosqlite
from pathlib import Path

from .models import Region, GameObject, Avatar, ClassID

DB_PATH = Path(__file__).parent / "habitat.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS regions (
                region_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                terrain_type INTEGER DEFAULT 0,
                x_size INTEGER DEFAULT 160,
                y_size INTEGER DEFAULT 255,
                orientation INTEGER DEFAULT 0,
                depth INTEGER DEFAULT 0,
                lighting INTEGER DEFAULT 1,
                neighbor_west INTEGER DEFAULT 0,
                neighbor_east INTEGER DEFAULT 0,
                neighbor_north INTEGER DEFAULT 0,
                neighbor_south INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS objects (
                noid INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                region_id INTEGER NOT NULL,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                orientation INTEGER DEFAULT 0,
                gr_state INTEGER DEFAULT 0,
                container_noid INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                style INTEGER DEFAULT 0,
                extra TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS avatars (
                noid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                x INTEGER DEFAULT 80,
                y INTEGER DEFAULT 130,
                orientation INTEGER DEFAULT 0,
                activity INTEGER DEFAULT 146,
                health INTEGER DEFAULT 255,
                bank_account INTEGER DEFAULT 5000,
                tokens_in_hand INTEGER DEFAULT 100,
                curse_type INTEGER DEFAULT 0,
                turf_region INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                travel INTEGER DEFAULT 0,
                teleports INTEGER DEFAULT 0,
                talk_count INTEGER DEFAULT 0,
                current_region INTEGER DEFAULT 1
            );
        """)
        await _migrate(db)
        await db.commit()


async def _migrate(db):
    """Add columns introduced after the first schema (idempotent)."""
    wanted = {
        "regions": [("weapons_free", "INTEGER DEFAULT 0")],
        "avatars": [
            ("curse_counter", "INTEGER DEFAULT 0"),
            ("curse_immune", "INTEGER DEFAULT 0"),
            ("true_head_style", "INTEGER DEFAULT 0"),
            ("style", "INTEGER DEFAULT 0"),
            ("customize", "TEXT DEFAULT '[0, 0]'"),
        ],
    }
    for table, cols in wanted.items():
        async with db.execute(f"PRAGMA table_info({table})") as cur:
            have = {r[1] for r in await cur.fetchall()}
        for name, decl in cols:
            if name not in have:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


async def get_region(region_id: int) -> Region | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM regions WHERE region_id = ?", (region_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["weapons_free"] = bool(d.get("weapons_free", 0))
            return Region(**d)


async def get_region_objects(region_id: int) -> list[GameObject]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM objects WHERE region_id = ?", (region_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                extra = json.loads(d.pop("extra", "{}"))
                d.pop("region_id", None)
                if "_noid" in extra:      # region-local noid saved by save_region_objects
                    d["noid"] = extra.pop("_noid")
                result.append(GameObject(**d, extra=extra))
            return result


async def save_region_objects(region_id: int, objects, avatar_names: dict | None = None):
    """Checkpoint every object of a region (PL/I checkpoint_object).

    Rows get fresh primary keys; the region-local noid is kept in
    extra["_noid"] so container references survive. An object held by an
    avatar (container_noid = avatar noid) is tagged extra["_held_by"] with the
    avatar name, because avatar noids change per session."""
    avatar_names = avatar_names or {}
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM objects WHERE region_id = ?", (region_id,))
        for o in objects:
            extra = dict(o.extra)
            extra.pop("_timeout", None)           # live Tact handle, not state
            extra["_noid"] = o.noid
            container = o.container_noid
            if container in avatar_names:
                extra["_held_by"] = avatar_names[container]
                container = 0
            await db.execute("""
                INSERT INTO objects (class_id, region_id, x, y, orientation,
                    gr_state, container_noid, position, style, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (int(o.class_id), region_id, o.x, o.y, o.orientation,
                  o.gr_state, container, o.position, o.style,
                  json.dumps(extra)))
        await db.commit()


async def save_region_flags(region) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE regions SET weapons_free = ? WHERE region_id = ?",
                         (1 if region.weapons_free else 0, region.region_id))
        await db.commit()


async def save_avatar(avatar: Avatar, region_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO avatars (name, x, y, orientation, activity, health,
                bank_account, tokens_in_hand, curse_type, curse_counter,
                curse_immune, true_head_style, style, customize, turf_region,
                deaths, kills, travel, teleports, talk_count, current_region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x=excluded.x, y=excluded.y, orientation=excluded.orientation,
                activity=excluded.activity, health=excluded.health,
                bank_account=excluded.bank_account,
                tokens_in_hand=excluded.tokens_in_hand,
                curse_type=excluded.curse_type,
                curse_counter=excluded.curse_counter,
                curse_immune=excluded.curse_immune,
                true_head_style=excluded.true_head_style,
                style=excluded.style, customize=excluded.customize,
                turf_region=excluded.turf_region,
                deaths=excluded.deaths, kills=excluded.kills,
                travel=excluded.travel, teleports=excluded.teleports,
                talk_count=excluded.talk_count, current_region=excluded.current_region
        """, (avatar.name, avatar.x, avatar.y, avatar.orientation,
              avatar.activity, avatar.health, avatar.bank_account,
              avatar.tokens_in_hand, int(avatar.curse_type), avatar.curse_counter,
              1 if avatar.curse_immune else 0, avatar.true_head_style,
              avatar.style, json.dumps(list(avatar.customize)),
              avatar.turf_region, avatar.deaths, avatar.kills, avatar.travel,
              avatar.teleports, avatar.talk_count, region_id))
        await db.commit()


async def load_avatar(name: str) -> tuple[Avatar, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM avatars WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            region_id = d.pop("current_region", 1)
            d["curse_immune"] = bool(d.get("curse_immune", 0))
            d["customize"] = json.loads(d.get("customize") or "[0, 0]")
            return Avatar(**d), region_id
