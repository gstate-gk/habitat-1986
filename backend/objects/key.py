"""Key. From class_key.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class KeyHandler(BaseObject):
    class_name = "key"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Use key on a locked door."""
        obj = region.get_object(noid)
        target_noid = args.get("target")
        if not obj or target_noid is None:
            return {"success": False}

        target = region.get_object(target_noid)
        if not target:
            return {"success": False, "error": "no target"}

        key_id = obj.extra.get("key_id", 0)
        lock_id = target.extra.get("key_noid", -1)

        if key_id != lock_id:
            return {"success": False, "error": "wrong key"}

        target.extra["locked"] = not target.extra.get("locked", False)
        state = "unlocked" if not target.extra["locked"] else "locked"

        await region.broadcast_all({
            "type": "KEY_USED",
            "noid": noid,
            "target": target_noid,
            "state": state,
        })
        return {"success": True, "state": state}
