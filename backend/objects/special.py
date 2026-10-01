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
        # Original class_hand_of_god has HELP only; DO is an illegal action.
        return {"success": False, "error": "illegal action: DO"}


class SexChangerHandler(BaseObject):
    """class_sex_changer: the SEXCHANGE action is in original_actions.py
    (toggles the avatar's sex bit; the old style cycling was an invention)."""

    async def handle_HELP(self, region, noid, args):
        return {"type": "identify", "class_name": "Sex Changer",
                "name": "Changes your sex."}
