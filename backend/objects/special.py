"""Special objects — hand_of_god, sex_changer, and readable variants.
PL/I: class_hand_of_god.pl1, class_sex_changer.pl1, class_plaque.pl1,
class_short_sign.pl1, class_book.pl1"""
from .base import BaseObject


class ReadableHandler(BaseObject):
    """Handler for plaque, short_sign, book — similar to sign/paper."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Readable")
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": obj.extra.get("text", "")[:30] if obj.extra else "",
        }

    async def handle_DO(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        text = obj.extra.get("text", "Nothing written here.") if obj.extra else "Nothing written here."
        author = obj.extra.get("author", "") if obj.extra else ""
        return {
            "type": "SIGN_READ",
            "text": text,
            "author": author,
        }

    async def handle_GRAB(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        if obj.class_id == ClassID.BOOK:
            avatar_noid = args.get("avatar_noid")
            obj.container_noid = avatar_noid
            await region.broadcast_all({"type": "GRAB", "noid": avatar_noid, "target": noid})
            return {"success": True}
        return {"type": "ACTION_RESULT", "text": "It's attached to the wall."}


class HandOfGodHandler(BaseObject):
    """The Hand of God — admin/moderator tool."""

    async def handle_HELP(self, region, noid, args):
        return {"type": "identify", "class_name": "Hand Of God", "name": "The divine hand."}

    async def handle_DO(self, region, noid, args):
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if avatar:
            avatar.health = 255
            avatar.tokens_in_hand = 1000
            await region.broadcast_all({
                "type": "SPEAK", "name": "Hand of God",
                "text": f"{avatar.name} has been blessed!",
            })
            return {"type": "ACTION_RESULT", "text": "Full heal + 1000 tokens!"}
        return {"type": "ACTION_RESULT", "text": "The hand waves ominously."}


class SexChangerHandler(BaseObject):
    """Change avatar appearance style."""

    async def handle_HELP(self, region, noid, args):
        return {"type": "identify", "class_name": "Sex Changer", "name": "Changes your appearance."}

    async def handle_DO(self, region, noid, args):
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if avatar:
            avatar.style = (avatar.style + 4) % 8
            return {"type": "ACTION_RESULT", "text": f"Your appearance has changed! (Style {avatar.style})"}
        return {"type": "ACTION_RESULT", "text": "Step inside to change."}
