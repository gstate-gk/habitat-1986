"""Region object handler. From class_region.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class RegionHandler(BaseObject):
    class_name = "region"

    async def handle_HELP(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        return {
            "success": True,
            "type": "identify",
            "class_name": "region",
            "name": region.region.name,
            "region_id": region.region.region_id,
        }
