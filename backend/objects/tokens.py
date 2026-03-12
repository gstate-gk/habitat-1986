"""Tokens (currency). From class_tokens.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class TokensHandler(BaseObject):
    class_name = "tokens"

    async def handle_GRAB(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """Pick up tokens — add to avatar's wallet."""
        obj = region.get_object(noid)
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if not obj or not avatar:
            return {"success": False}

        amount = obj.extra.get("denomination", 0)
        avatar.tokens_in_hand += amount
        region.remove_object(noid)

        return {
            "success": True,
            "type": "TOKENS_PICKED",
            "amount": amount,
            "total": avatar.tokens_in_hand,
        }
