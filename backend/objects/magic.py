"""Magic items — amulet, ring, crystal_ball, magic_lamp/staff/wand.
PL/I: magic.pl1 (903 lines) implements 29 magic spells.
We implement a simplified subset."""
import random
from .base import BaseObject


SPELL_EFFECTS = [
    "A warm glow surrounds you.",
    "Sparks fly from the item!",
    "You feel a surge of energy.",
    "The air shimmers briefly.",
    "A faint melody plays.",
    "You feel lighter on your feet.",
    "Colors swirl around you.",
    "The ground trembles slightly.",
    "A cool breeze passes through.",
    "You sense hidden things nearby.",
]


class MagicHandler(BaseObject):
    """Handler for magic items."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Magic Item")
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": "It hums with power." if obj.gr_state else "",
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
        """Cast a spell / use magic item."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)

        if obj.class_id == ClassID.CRYSTAL_BALL:
            # Reveal info about region
            n_objects = len(region.objects)
            n_avatars = len(region.avatars)
            return {
                "type": "ACTION_RESULT",
                "text": f"The crystal ball reveals: {n_objects} objects, {n_avatars} beings in this region.",
            }

        if obj.class_id == ClassID.AMULET:
            # Healing
            if avatar:
                heal = random.randint(20, 60)
                avatar.health = min(255, avatar.health + heal)
                return {"type": "ACTION_RESULT", "text": f"The amulet glows! You heal {heal} HP."}

        if obj.class_id == ClassID.RING:
            # Random effect
            effect = random.choice(SPELL_EFFECTS)
            if avatar:
                avatar.health = min(255, avatar.health + 10)
            return {"type": "ACTION_RESULT", "text": effect}

        if obj.class_id in (ClassID.MAGIC_LAMP, ClassID.MAGIC_STAFF, ClassID.MAGIC_WAND):
            # Offensive magic — damage random target
            targets = [a for a in region.avatars.values() if a.noid != avatar_noid]
            if targets:
                target = random.choice(targets)
                damage = random.randint(15, 35)
                target.health = max(0, target.health - damage)
                await region.broadcast_all({
                    "type": "GUN_SHOT", "shooter": avatar_noid,
                    "target_noid": target.noid, "damage": damage,
                })
                return {"type": "ACTION_RESULT", "text": f"Magic blast hits {target.name} for {damage}!"}
            else:
                effect = random.choice(SPELL_EFFECTS)
                await region.broadcast_all({"type": "SPEAK", "name": "Magic", "text": effect})
                return {"type": "ACTION_RESULT", "text": effect}

        # Default
        effect = random.choice(SPELL_EFFECTS)
        return {"type": "ACTION_RESULT", "text": effect}
