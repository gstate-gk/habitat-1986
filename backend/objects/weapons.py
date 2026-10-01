"""Non-gun weapons — knife, club, boomerang, stun_gun, fake_gun, grenade.
PL/I: class_knife.pl1, class_club.pl1, etc.

Attack/stun/pull-pin/throw actions are in original_actions.py (original
semantics: flat 20 damage, no per-weapon damage table). This handler keeps
HELP/GRAB/HAND."""
from .base import BaseObject


class WeaponHandler(BaseObject):
    """Handler for melee and thrown weapons."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Weapon")
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": "",
        }

    async def handle_GRAB(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        avatar_noid = args.get("avatar_noid")
        obj.container_noid = avatar_noid
        await region.broadcast_all({
            "type": "GRAB", "noid": avatar_noid, "target": noid,
        })
        return {"success": True}

    async def handle_HAND(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        x = args.get("x", obj.x)
        y = args.get("y", obj.y)
        obj.container_noid = 0
        obj.x = x
        obj.y = y
        await region.broadcast_all({
            "type": "HAND", "noid": args.get("avatar_noid"), "target": noid,
            "x": x, "y": y,
        })
        return {"success": True}
