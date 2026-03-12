"""Non-gun weapons — melee/thrown weapons.
Covers: knife, club, boomerang, stun_gun, fake_gun, grenade.
PL/I: class_knife.pl1, class_club.pl1, etc."""
import random
from .base import BaseObject


class WeaponHandler(BaseObject):
    """Handler for melee and thrown weapons."""

    DAMAGE_TABLE = {
        44: 15,   # KNIFE
        16: 20,   # CLUB
        11: 12,   # BOOMERANG
        91: 5,    # STUN_GUN (stun, low damage)
        27: 0,    # FAKE_GUN (no damage)
        35: 40,   # GRENADE (high damage, single use)
    }

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

    async def handle_DO(self, region, noid, args):
        """Attack with weapon."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        avatar_noid = args.get("avatar_noid")
        base_damage = self.DAMAGE_TABLE.get(obj.class_id, 10)

        if obj.class_id == ClassID.FAKE_GUN:
            await region.broadcast_all({
                "type": "SPEAK", "name": "Fake Gun", "text": "BANG! (just kidding)",
            })
            return {"type": "ACTION_RESULT", "text": "It's a fake! No damage dealt."}

        if obj.class_id == ClassID.GRENADE:
            # Grenade damages all avatars in region except thrower
            for av in list(region.avatars.values()):
                if av.noid != avatar_noid:
                    damage = base_damage + random.randint(0, 20)
                    av.health = max(0, av.health - damage)
                    await region.broadcast_all({
                        "type": "GUN_SHOT", "shooter": avatar_noid,
                        "target_noid": av.noid, "damage": damage,
                    })
            region.remove_object(noid)  # grenade is consumed
            return {"type": "ACTION_RESULT", "text": "BOOM! The grenade explodes!"}

        # Melee/thrown — find nearest other avatar
        attacker = region.get_avatar(avatar_noid)
        target = None
        min_dist = float("inf")
        for av in region.avatars.values():
            if av.noid == avatar_noid:
                continue
            dist = abs(av.x - attacker.x) + abs(av.y - attacker.y)
            if dist < min_dist:
                min_dist = dist
                target = av

        if not target:
            return {"type": "ACTION_RESULT", "text": "No target in range."}

        damage = base_damage + random.randint(0, 10)
        if obj.class_id == ClassID.STUN_GUN:
            target.stun_count = min(255, target.stun_count + 30)
            damage = 5
        target.health = max(0, target.health - damage)

        await region.broadcast_all({
            "type": "GUN_SHOT", "shooter": avatar_noid,
            "target_noid": target.noid, "damage": damage,
        })
        return {"type": "ACTION_RESULT", "text": f"Hit {target.name} for {damage} damage!"}
