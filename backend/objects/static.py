"""Static/scenery objects — no special interaction beyond HELP (identify).
Covers: tree, bush, plant, rock, river, pond, fountain, sky, roof, bridge,
fence, wall, window, building, streetlamp, flat, trapezoid, super_trapezoid,
floor_lamp, countertop, table, bed, couch, chair, aquarium, hot_tub,
stereo, jukebox, picture, flag, knick_knack, elevator, hole, sidewalk.
PL/I: these classes typically only implement generic_HELP."""
from .base import BaseObject


class StaticHandler(BaseObject):
    """Generic handler for non-interactive scenery and furniture."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Object")
        label = obj.extra.get("text", "") if obj.extra else ""
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": label,
        }

    async def handle_DO(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        cid = obj.class_id
        if cid == ClassID.JUKEBOX:
            await region.broadcast_all({"type": "SOUND", "noid": noid, "sound": "music"})
            return {"type": "ACTION_RESULT", "text": "The jukebox plays a tune!"}
        if cid == ClassID.FOUNTAIN:
            return {"type": "ACTION_RESULT", "text": "Water splashes gently."}
        if cid == ClassID.HOT_TUB:
            return {"type": "ACTION_RESULT", "text": "The water is warm and inviting."}
        if cid == ClassID.ELEVATOR:
            return {"type": "ACTION_RESULT", "text": "The elevator hums softly."}
        return {"type": "ACTION_RESULT", "text": "Nothing happens."}
