"""Sign/plaque. From class_sign.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class SignHandler(BaseObject):
    class_name = "sign"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Read the sign."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        return {
            "success": True,
            "type": "SIGN_READ",
            "noid": noid,
            "text": obj.extra.get("text", ""),
        }
