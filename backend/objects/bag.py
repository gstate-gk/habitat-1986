"""Bag/container. From generic container pattern."""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class BagHandler(BaseObject):
    class_name = "bag"
    capacity = 5

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Open bag — list contents."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        contents = [
            {"noid": o.noid, "class_id": o.class_id, "class_name": o.extra.get("class_name", "object")}
            for o in region.objects.values()
            if o.container_noid == noid
        ]
        return {
            "success": True,
            "type": "CONTAINER_OPEN",
            "noid": noid,
            "contents": contents,
        }

    async def handle_PUT(self, region: "RegionProcessor",
                         noid: int, args: dict) -> dict:
        """Put item into bag."""
        obj = region.get_object(noid)
        target_noid = args.get("target")
        if not obj or target_noid is None:
            return {"success": False}

        contents_count = sum(1 for o in region.objects.values() if o.container_noid == noid)
        if contents_count >= self.capacity:
            return {"success": False, "error": "container full"}

        target = region.get_object(target_noid)
        if not target:
            return {"success": False, "error": "object not found"}

        target.container_noid = noid
        return {"success": True, "type": "CONTAINER_PUT"}

    async def handle_GRAB(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """Take item from bag."""
        target_noid = args.get("target")
        avatar_noid = args.get("avatar_noid")
        if target_noid is None:
            return {"success": False}
        target = region.get_object(target_noid)
        if not target or target.container_noid != noid:
            return {"success": False, "error": "not in container"}
        target.container_noid = avatar_noid if avatar_noid else 0
        return {"success": True, "type": "CONTAINER_GRAB", "target": target_noid}
