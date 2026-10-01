"""
Region processor — the heart of the Habitat server.
Converted from: regionproc.pl1 (5,455 lines)

Original PL/I event loop:
    regionproc: procedure options(main);
        do while (true);
            call s$task_wait_event(Master_ei, wait_forever, task, event, ...);
            if (task = server_event) then call handle_msg;
            else if (task = tact_event) then call ProcessTact;
        end;
    end;

Python equivalent: asyncio event loop + WebSocket message dispatch.
"""
from __future__ import annotations
import asyncio
import heapq
import itertools
import time
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

from .models import Avatar, Region, GameObject, ClassID
from .objects.base import OBJECT_REGISTRY


class RegionProcessor:
    """Manages a single region (room) and its objects/users.

    PL/I equivalents:
        ObjList(0:254)  → self.objects
        UserList(0:5)   → self.users
        Region          → self.region
    """

    def __init__(self, region: Region):
        self.region = region
        self.objects: dict[int, GameObject] = {}  # noid → object
        self.avatars: dict[int, Avatar] = {}      # noid → avatar
        self.users: dict[int, WebSocket] = {}     # noid → websocket
        self._next_noid = 10
        # PL/I Tact: timed callbacks. Delay unit is seconds
        # (class_magic_lamp.pl1: GENIE_TIMEOUT 30 "30 seconds").
        self._tacts: list = []
        self._tact_seq = itertools.count()
        self._tact_live: set[int] = set()
        self.clock: Callable[[], float] = time.monotonic
        # checkpoint flag (PL/I gen_flags(MODIFIED) -> checkpoint_object)
        self.dirty = False
        # objects carried by avatars who are offline: avatar name -> objects
        self.stash: dict[str, list[GameObject]] = {}

    def alloc_noid(self) -> int:
        while (self._next_noid in self.objects
               or self._next_noid in self.avatars):
            self._next_noid += 1
        noid = self._next_noid
        self._next_noid += 1
        return noid

    # --- Tact (timer events) ---

    def tact(self, delay: float, callback: Callable, *args) -> int:
        """PL/I: call Tact(proc, arg, delay). Returns a handle.
        callback is an async function called as callback(region, *args)."""
        handle = next(self._tact_seq)
        heapq.heappush(self._tacts, (self.clock() + delay, handle, callback, args))
        self._tact_live.add(handle)
        return handle

    def clear_tact(self, handle: Optional[int]) -> bool:
        """PL/I: ClearTactByValue."""
        if handle in self._tact_live:
            self._tact_live.discard(handle)
            return True
        return False

    async def process_tact(self, now: Optional[float] = None) -> int:
        """PL/I: ProcessTact. Runs every callback that is due; returns count."""
        now = self.clock() if now is None else now
        ran = 0
        while self._tacts and self._tacts[0][0] <= now:
            _, handle, callback, args = heapq.heappop(self._tacts)
            if handle not in self._tact_live:
                continue
            self._tact_live.discard(handle)
            try:
                await callback(self, *args)
            except Exception as e:  # keep the event loop alive
                print(f"tact error in region {self.region.region_id}: {e!r}")
            ran += 1
        return ran

    async def tact_loop(self, interval: float = 1.0):
        """asyncio form of the regionproc.pl1 s$task_wait_event loop."""
        while True:
            await asyncio.sleep(interval)
            await self.process_tact()

    def add_object(self, obj: GameObject) -> int:
        if obj.noid == 0:
            obj.noid = self.alloc_noid()
        self.objects[obj.noid] = obj
        return obj.noid

    def remove_object(self, noid: int):
        self.objects.pop(noid, None)

    def get_object(self, noid: int) -> Optional[GameObject]:
        return self.objects.get(noid) or self._avatar_as_object(noid)

    def _avatar_as_object(self, noid: int) -> Optional[GameObject]:
        avatar = self.avatars.get(noid)
        if not avatar:
            return None
        return GameObject(
            noid=avatar.noid, class_id=ClassID.AVATAR,
            x=avatar.x, y=avatar.y, orientation=avatar.orientation,
            gr_state=avatar.activity, container_noid=0,
        )

    def get_avatar(self, noid: int) -> Optional[Avatar]:
        return self.avatars.get(noid)

    def add_avatar(self, avatar: Avatar, ws: WebSocket) -> int:
        """PL/I: initiate_avatar_creation in hatchery.pl1"""
        if avatar.noid == 0:
            avatar.noid = self.alloc_noid()
        self.avatars[avatar.noid] = avatar
        self.users[avatar.noid] = ws
        return avatar.noid

    def remove_avatar(self, noid: int):
        self.avatars.pop(noid, None)
        self.users.pop(noid, None)

    def get_state(self) -> dict:
        """Full region state for client initialization."""
        return {
            "region": {
                "id": self.region.region_id,
                "name": self.region.name,
                "x_size": self.region.x_size,
                "y_size": self.region.y_size,
                "terrain_type": self.region.terrain_type,
                "lighting": self.region.lighting,
                "neighbors": {
                    "west": self.region.neighbor_west,
                    "east": self.region.neighbor_east,
                    "north": self.region.neighbor_north,
                    "south": self.region.neighbor_south,
                },
            },
            "objects": [
                {
                    "noid": o.noid,
                    "class_id": o.class_id,
                    "x": o.x, "y": o.y,
                    "orientation": o.orientation,
                    "gr_state": o.gr_state,
                    "container_noid": o.container_noid,
                    "style": o.style,
                    "extra": o.extra,
                }
                for o in self.objects.values()
            ],
            "avatars": [
                {
                    "noid": a.noid,
                    "name": a.name,
                    "x": a.x, "y": a.y,
                    "orientation": a.orientation,
                    "activity": a.activity,
                    "health": a.health,
                    "tokens": a.tokens_in_hand,
                }
                for a in self.avatars.values()
            ],
        }

    async def handle_message(self, sender_noid: int, msg: dict) -> dict:
        """Main message dispatcher.

        PL/I: handle_msg in regionproc.pl1
            current_noid = msg_buffer(3);
            current_request = msg_buffer(4);
            call Class_Table(object.class).actions->a(current_request);
        """
        action = msg.get("action", "")
        target_noid = msg.get("noid", sender_noid)

        # Determine class of target object
        obj = self.get_object(target_noid)
        avatar = self.avatars.get(target_noid)

        if avatar:
            class_id = ClassID.AVATAR
        elif obj:
            class_id = obj.class_id
        else:
            return {"success": False, "error": "object not found"}

        handler = OBJECT_REGISTRY.get(class_id)
        if not handler:
            return {"success": False, "error": f"no handler for class {class_id}"}

        args = msg.get("args", {})
        args["avatar_noid"] = sender_noid

        result = await handler.dispatch(action, self, target_noid, args)
        if action != "HELP":
            self.dirty = True

        # Handle region changes (door/teleport)
        if result.get("type") == "region_change":
            result["_region_change"] = True

        return result

    # --- Messaging (from messages.pl1) ---

    async def broadcast_all(self, msg: dict):
        """PL/I: b_msg_N — broadcast to all users in region."""
        dead = []
        for noid, ws in self.users.items():
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(noid)
        for noid in dead:
            self.users.pop(noid, None)

    async def broadcast(self, exclude_noid: int, msg: dict):
        """PL/I: e_msg_N — broadcast excluding one user."""
        dead = []
        for noid, ws in self.users.items():
            if noid == exclude_noid:
                continue
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(noid)
        for noid in dead:
            self.users.pop(noid, None)

    async def send_to(self, noid: int, msg: dict):
        """PL/I: p_msg_N — point-to-point to specific user."""
        ws = self.users.get(noid)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                self.users.pop(noid, None)

    # --- carried objects across leave \/ region change ---

    def detach_held(self, avatar_noid: int, name: str) -> list[GameObject]:
        """Take the objects an avatar holds out of the region (leave/disconnect).
        They are kept in self.stash under the avatar name and saved with it."""
        held = [o for o in self.objects.values() if o.container_noid == avatar_noid]
        for o in held:
            self.objects.pop(o.noid, None)
            o.extra["_held_by"] = name
        if held:
            self.stash.setdefault(name, []).extend(held)
            self.dirty = True
        return held
