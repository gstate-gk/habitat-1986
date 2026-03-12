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
from typing import Optional
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

    def alloc_noid(self) -> int:
        noid = self._next_noid
        self._next_noid += 1
        return noid

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
