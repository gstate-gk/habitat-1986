"""Portable items — can be picked up (GRAB) and put down (HAND).
Covers: flashlight, shovel, compass, tape, glue, spray_can, matchbook,
bottle, drugs, skateboard, frisbee, ball, windup_toy, movie_camera,
ticket, game_piece, die, instant_object, escape_dev, sensor,
security_dev, head, gemstone.
PL/I: these implement generic_HELP + generic_GRAB."""
from .base import BaseObject


class PortableHandler(BaseObject):
    """Generic handler for items that can be picked up."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Object")
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": obj.extra.get("text", "") if obj.extra else "",
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
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        cid = obj.class_id
        if cid == ClassID.FLASHLIGHT:
            obj.gr_state = 1 - obj.gr_state
            return {"type": "ACTION_RESULT", "text": f"Flashlight {'on' if obj.gr_state else 'off'}."}
        if cid == ClassID.COMPASS:
            return {"type": "ACTION_RESULT", "text": "The compass points North."}
        if cid == ClassID.DIE:
            import random
            roll = random.randint(1, 6)
            await region.broadcast_all({"type": "SPEAK", "name": "Die", "text": f"Rolled a {roll}!"})
            return {"type": "ACTION_RESULT", "text": f"You rolled a {roll}."}
        if cid == ClassID.WINDUP_TOY:
            await region.broadcast_all({"type": "SOUND", "noid": noid, "sound": "windup"})
            return {"type": "ACTION_RESULT", "text": "The toy winds up and walks around!"}
        if cid == ClassID.DRUGS:
            avatar = region.get_avatar(args.get("avatar_noid"))
            if avatar:
                avatar.health = min(255, avatar.health + 50)
            return {"type": "ACTION_RESULT", "text": "You feel better. (+50 HP)"}
        return {"type": "ACTION_RESULT", "text": "Nothing happens."}
