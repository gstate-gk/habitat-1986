"""Vending machine. From class_vendo_front.pl1
PL/I: vendo_VSELECT, vendo_PAY"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class VendoHandler(BaseObject):
    class_name = "vendo"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """PL/I: vendo_VSELECT — cycle through items."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}

        items = obj.extra.get("items", [])
        prices = obj.extra.get("prices", [])
        if not items:
            return {"success": False, "error": "empty"}

        display = obj.extra.get("display_item", 0)
        display = (display + 1) % len(items)
        obj.extra["display_item"] = display

        return {
            "success": True,
            "type": "VENDO_DISPLAY",
            "noid": noid,
            "item_name": items[display] if display < len(items) else "???",
            "item_price": prices[display] if display < len(prices) else 0,
            "slot": display,
        }

    async def handle_PAY(self, region: "RegionProcessor",
                         noid: int, args: dict) -> dict:
        """PL/I: vendo_PAY — purchase displayed item."""
        obj = region.get_object(noid)
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if not obj or not avatar:
            return {"success": False}

        display = obj.extra.get("display_item", 0)
        prices = obj.extra.get("prices", [])
        items = obj.extra.get("items", [])
        if display >= len(prices) or display >= len(items):
            return {"success": False, "error": "invalid item"}

        price = prices[display]
        if avatar.tokens_in_hand < price:
            return {"success": False, "error": "insufficient tokens"}

        avatar.tokens_in_hand -= price
        obj.extra["take"] = obj.extra.get("take", 0) + price
        purchased_item = items[display]

        await region.broadcast_all({
            "type": "VENDO_PURCHASE",
            "noid": noid,
            "buyer": avatar.name,
            "item": purchased_item,
        })
        return {
            "success": True,
            "type": "VENDO_BOUGHT",
            "item": purchased_item,
            "price": price,
            "tokens": avatar.tokens_in_hand,
        }
