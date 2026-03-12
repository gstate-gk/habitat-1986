"""
Avatar object handler.
Converted from: chip/habitat/stratus/class_avatar.pl1 (483 lines)

Original PL/I actions:
    Class_Table(I).actions->a(HELP) = avatar_IDENTIFY;
    Class_Table(I).actions->a(GRAB) = avatar_GRAB;
    Class_Table(I).actions->a(HAND) = avatar_HAND;
    Class_Table(I).actions->a(POSTURE) = avatar_POSTURE;
    Class_Table(I).actions->a(SPEAK) = avatar_SPEAK;
    Class_Table(I).actions->a(WALK) = avatar_WALK;
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject
from ..models import CurseType, Posture

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


def buzzify(text: str) -> str:
    """PL/I: buzzify — CURSE_FLY replaces all letters with 'z'.
    translate(text, 'zzz...', 'abc...')"""
    result = []
    for ch in text:
        if ch.isalpha():
            result.append('Z' if ch.isupper() else 'z')
        elif ch.isdigit():
            result.append('z')
        else:
            result.append(ch)
    return "".join(result)


class AvatarHandler(BaseObject):
    class_name = "avatar"
    capacity = 5  # AVATAR_CAPACITY — hands + head

    async def handle_WALK(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """PL/I: avatar_WALK — move avatar to new position."""
        avatar = region.get_avatar(noid)
        if not avatar:
            return {"success": False}

        x = args.get("x", avatar.x)
        y = args.get("y", avatar.y)

        if avatar.stun_count > 0:
            avatar.stun_count -= 1
            return {"success": False, "error": "stunned"}

        avatar.x = max(0, min(x, region.region.x_size))
        avatar.y = max(0, min(y, region.region.y_size))

        await region.broadcast(noid, {
            "type": "WALK",
            "noid": noid,
            "x": avatar.x,
            "y": avatar.y,
        })
        return {"success": True, "x": avatar.x, "y": avatar.y}

    async def handle_POSTURE(self, region: "RegionProcessor",
                             noid: int, args: dict) -> dict:
        """PL/I: avatar_POSTURE — sit, stand, turn."""
        avatar = region.get_avatar(noid)
        if not avatar:
            return {"success": False}

        new_posture = args.get("posture", Posture.STAND_FRONT)
        avatar.activity = new_posture

        await region.broadcast(noid, {
            "type": "POSTURE",
            "noid": noid,
            "posture": new_posture,
        })
        return {"success": True, "posture": new_posture}

    async def handle_SPEAK(self, region: "RegionProcessor",
                           noid: int, args: dict) -> dict:
        """PL/I: avatar_SPEAK — chat with curse processing."""
        avatar = region.get_avatar(noid)
        if not avatar:
            return {"success": False}

        text = args.get("text", "")
        avatar.talk_count += 1

        # Curse processing (from original PL/I)
        if avatar.curse_type == CurseType.SMILEY:
            text = "Have a nice day!"
        elif avatar.curse_type == CurseType.FLY:
            text = buzzify(text)

        await region.broadcast_all({
            "type": "SPEAK",
            "noid": noid,
            "name": avatar.name,
            "text": text,
        })
        return {"success": True, "text": text}

    async def handle_GRAB(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """PL/I: avatar_GRAB — pick up an object."""
        avatar = region.get_avatar(noid)
        target_noid = args.get("target")
        if not avatar or target_noid is None:
            return {"success": False}

        obj = region.get_object(target_noid)
        if not obj:
            return {"success": False, "error": "object not found"}

        obj.container_noid = noid
        await region.broadcast(noid, {
            "type": "GRAB",
            "noid": noid,
            "target": target_noid,
        })
        return {"success": True, "target": target_noid}

    async def handle_HAND(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """PL/I: avatar_HAND — put down or give object."""
        avatar = region.get_avatar(noid)
        target_noid = args.get("target")
        if not avatar or target_noid is None:
            return {"success": False}

        obj = region.get_object(target_noid)
        if not obj or obj.container_noid != noid:
            return {"success": False, "error": "not holding"}

        x = args.get("x", avatar.x)
        y = args.get("y", avatar.y)
        obj.container_noid = 0  # THE_REGION
        obj.x = x
        obj.y = y

        await region.broadcast(noid, {
            "type": "HAND",
            "noid": noid,
            "target": target_noid,
            "x": x, "y": y,
        })
        return {"success": True}

    async def handle_HELP(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        avatar = region.get_avatar(noid)
        if not avatar:
            return {"success": False}
        return {
            "success": True,
            "type": "identify",
            "class_name": "avatar",
            "name": avatar.name,
            "health": avatar.health,
            "bank_account": avatar.bank_account,
        }
