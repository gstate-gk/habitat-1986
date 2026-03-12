"""Container objects — can hold other items.
Covers: box, chest, safe, display_case, garbage_can, dropbox.
PL/I: these implement OPEN/CLOSE + container operations."""
from .base import BaseObject


class ContainerHandler(BaseObject):
    """Handler for container objects (box, chest, safe, etc.)."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Container")
        contents = [o for o in region.objects.values() if o.container_noid == noid]
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": f"Contains {len(contents)} item(s)",
        }

    async def handle_DO(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        obj.gr_state = 1 - obj.gr_state
        state = "open" if obj.gr_state else "closed"
        await region.broadcast_all({
            "type": "DOOR_TOGGLE", "noid": noid, "open": obj.gr_state == 1,
        })
        return {"type": "ACTION_RESULT", "text": f"Container is now {state}."}

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
