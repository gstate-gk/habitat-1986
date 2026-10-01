"""Interactive machines — coke_machine, fortune_machine, pawn_machine,
changomatic, switch.
PL/I: class_coke_machine.pl1, class_fortune_machine.pl1, etc.

The original per-class actions (PAY, MUNCH, CHANGE) live in
original_actions.py and are dispatched before this handler. The earlier
inventions (coke +20 HP, 10 made-up fortunes, appearance cycling) were
removed; the original has 90 fortunes (fortunes_data.py) and no HP effect.
SWITCH is kept as a web-only addition (no class_switch action in the original
table that this port converts)."""
from .base import BaseObject


class MachineHandler(BaseObject):
    """Handler for interactive machines."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        names = {v: k for k, v in ClassID.__members__.items()}
        name = names.get(obj.class_id, "Machine")
        return {
            "type": "identify",
            "class_name": name.replace("_", " ").title(),
            "name": "",
        }

    async def handle_DO(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        if obj.class_id == ClassID.SWITCH:
            obj.gr_state = 1 - obj.gr_state
            state = "ON" if obj.gr_state else "OFF"
            return {"type": "ACTION_RESULT", "text": f"Switch is now {state}."}
        return {"type": "ACTION_RESULT", "text": "The machine hums quietly."}
