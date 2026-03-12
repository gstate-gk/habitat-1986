"""Teleport booth. From class_teleport.pl1
PL/I: TELEPORT_COST = 10, PORT_READY = 0, PORT_ACTIVE = 1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor

TELEPORT_COST = 10


class TeleportHandler(BaseObject):
    class_name = "teleport"

    async def handle_PAY(self, region: "RegionProcessor",
                         noid: int, args: dict) -> dict:
        """PL/I: teleport_PAY — pay to activate booth."""
        obj = region.get_object(noid)
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if not obj or not avatar:
            return {"success": False}

        if obj.gr_state != 0:  # not ready
            return {"success": False, "error": "booth busy"}

        if avatar.tokens_in_hand < TELEPORT_COST:
            return {"success": False, "error": "insufficient tokens"}

        avatar.tokens_in_hand -= TELEPORT_COST
        obj.gr_state = 1
        obj.extra["take"] = obj.extra.get("take", 0) + TELEPORT_COST

        await region.send_to(avatar_noid, {
            "type": "TELEPORT_READY",
            "noid": noid,
        })
        return {"success": True}

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """PL/I: teleport_ZAPTO — teleport to destination."""
        obj = region.get_object(noid)
        if not obj or obj.gr_state != 1:
            return {"success": False, "error": "not activated"}

        destination = args.get("destination", obj.extra.get("destination", 0))
        if destination == 0:
            return {"success": False, "error": "no destination"}

        obj.gr_state = 0  # reset to ready
        avatar_noid = args.get("avatar_noid")

        if avatar_noid is not None:
            avatar = region.get_avatar(avatar_noid)
            if avatar:
                avatar.teleports += 1

        return {
            "success": True,
            "type": "region_change",
            "destination": destination,
            "avatar_noid": avatar_noid,
            "transition": "teleport",
        }
