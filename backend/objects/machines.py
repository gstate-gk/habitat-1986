"""Interactive machines — coke_machine, fortune_machine, pawn_machine,
changomatic, switch.
PL/I: class_coke_machine.pl1, class_fortune_machine.pl1, etc."""
import random
from .base import BaseObject

FORTUNES = [
    "A great adventure awaits you.",
    "Beware of the ghost in the park.",
    "Your bank balance will grow.",
    "A stranger will offer you a deal.",
    "The stars align in your favor.",
    "Avoid dark alleys after midnight.",
    "Fortune favors the bold.",
    "You will find what you seek.",
    "A friend in need is a friend indeed.",
    "The answer is 42.",
]


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
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)

        if obj.class_id == ClassID.COKE_MACHINE:
            if avatar and avatar.tokens_in_hand >= 5:
                avatar.tokens_in_hand -= 5
                avatar.health = min(255, avatar.health + 20)
                return {"type": "ACTION_RESULT", "text": "You buy a Coke. Refreshing! (+20 HP, -5 tokens)"}
            return {"type": "ACTION_RESULT", "text": "Not enough tokens. (Need 5)"}

        if obj.class_id == ClassID.FORTUNE_MACHINE:
            if avatar and avatar.tokens_in_hand >= 2:
                avatar.tokens_in_hand -= 2
                fortune = random.choice(FORTUNES)
                return {"type": "ACTION_RESULT", "text": f"Fortune: \"{fortune}\" (-2 tokens)"}
            return {"type": "ACTION_RESULT", "text": "Insert 2 tokens for your fortune."}

        if obj.class_id == ClassID.PAWN_MACHINE:
            # Sell held item
            return {"type": "ACTION_RESULT", "text": "The pawn machine accepts items for tokens."}

        if obj.class_id == ClassID.CHANGOMATIC:
            # Change avatar appearance
            if avatar:
                avatar.style = (avatar.style + 1) % 8
                return {"type": "ACTION_RESULT", "text": f"Your appearance changed! (Style {avatar.style})"}
            return {"type": "ACTION_RESULT", "text": "Step inside to change your look!"}

        if obj.class_id == ClassID.SWITCH:
            obj.gr_state = 1 - obj.gr_state
            state = "ON" if obj.gr_state else "OFF"
            return {"type": "ACTION_RESULT", "text": f"Switch is now {state}."}

        return {"type": "ACTION_RESULT", "text": "The machine hums quietly."}

    async def handle_PAY(self, region, noid, args):
        """Pay to use machine."""
        return await self.handle_DO(region, noid, args)
