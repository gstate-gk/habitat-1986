"""Paper (writable). From class_paper.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class PaperHandler(BaseObject):
    class_name = "paper"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Read paper."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        return {
            "success": True,
            "type": "PAPER_READ",
            "noid": noid,
            "text": obj.extra.get("text", ""),
            "author": obj.extra.get("author", ""),
        }

    async def handle_PUT(self, region: "RegionProcessor",
                         noid: int, args: dict) -> dict:
        """Write on paper."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        text = args.get("text", "")
        author = args.get("author", "")
        obj.extra["text"] = text
        obj.extra["author"] = author
        return {"success": True, "type": "PAPER_WRITTEN"}
