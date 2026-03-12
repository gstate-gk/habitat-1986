"""Wearable items — clothing and accessories.
Covers: hat, shirt, jacket, pants, head, gemstone.
PL/I: these implement WEAR/REMOVE actions."""
from .base import BaseObject


class WearableHandler(BaseObject):
    """Handler for clothing and accessories."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Clothing")
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

    async def handle_DO(self, region, noid, args):
        """Wear/remove item."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        if obj.gr_state == 0:
            obj.gr_state = 1
            return {"type": "ACTION_RESULT", "text": "You put it on."}
        else:
            obj.gr_state = 0
            return {"type": "ACTION_RESULT", "text": "You take it off."}
