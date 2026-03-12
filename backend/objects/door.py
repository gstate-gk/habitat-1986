"""Door handler. From class_door.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class DoorHandler(BaseObject):
    class_name = "door"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """PL/I: generic_OPEN/CLOSE — toggle door state."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}

        if obj.extra.get("locked"):
            return {"success": False, "error": "locked"}

        is_open = obj.gr_state == 1
        obj.gr_state = 0 if is_open else 1

        await region.broadcast_all({
            "type": "DOOR_TOGGLE",
            "noid": noid,
            "open": obj.gr_state == 1,
        })
        return {"success": True, "open": obj.gr_state == 1}

    async def handle_GO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Walk through door to connected region."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}

        connection = obj.extra.get("connection", 0)
        if connection == 0:
            return {"success": False, "error": "no connection"}

        if obj.gr_state == 0:  # closed
            obj.gr_state = 1  # auto-open
            await region.broadcast_all({
                "type": "DOOR_TOGGLE", "noid": noid, "open": True,
            })

        avatar_noid = args.get("avatar_noid")
        return {
            "success": True,
            "type": "region_change",
            "destination": connection,
            "avatar_noid": avatar_noid,
        }
