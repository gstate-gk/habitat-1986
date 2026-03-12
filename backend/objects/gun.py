"""Gun. From class_gun.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class GunHandler(BaseObject):
    class_name = "gun"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """PL/I: gun_SHOOT — fire at target."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}

        ammo = obj.extra.get("ammo", 0)
        if ammo <= 0:
            return {"success": False, "error": "no ammo"}

        target_noid = args.get("target")
        if target_noid is None:
            return {"success": False, "error": "no target"}

        target_avatar = region.get_avatar(target_noid)
        if not target_avatar:
            return {"success": False, "error": "invalid target"}

        obj.extra["ammo"] = ammo - 1
        damage = obj.extra.get("damage", 10)
        target_avatar.health = max(0, target_avatar.health - damage)

        await region.broadcast_all({
            "type": "GUN_SHOT",
            "shooter_noid": obj.container_noid,
            "target_noid": target_noid,
            "damage": damage,
        })

        result = {
            "success": True,
            "damage": damage,
            "target_health": target_avatar.health,
            "ammo": obj.extra["ammo"],
        }

        if target_avatar.health <= 0:
            result["target_dead"] = True
            await region.broadcast_all({
                "type": "AVATAR_DEATH",
                "noid": target_noid,
                "name": target_avatar.name,
            })

        return result
