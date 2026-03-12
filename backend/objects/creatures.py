"""NPC creatures — ghost, house_cat, bureaucrat.
PL/I: class_ghost.pl1, class_house_cat.pl1, class_bureaucrat.pl1"""
import random
from .base import BaseObject

GHOST_MESSAGES = [
    "OooOOOooo...",
    "Begone, mortal!",
    "I haunt these halls...",
    "Boo!",
    "The afterlife is boring.",
]

CAT_ACTIONS = [
    "The cat purrs contentedly.",
    "The cat ignores you completely.",
    "The cat rubs against your leg.",
    "The cat hisses and runs away.",
    "The cat stares at you judgmentally.",
    "The cat yawns.",
]

BUREAUCRAT_RESPONSES = [
    "Please fill out form 27B/6.",
    "Your request is being processed.",
    "That's not my department.",
    "Come back between 9 and 5.",
    "You need three forms of ID.",
    "The committee will review your case.",
]


class CreatureHandler(BaseObject):
    """Handler for NPC creatures."""

    async def handle_HELP(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        if obj.class_id == ClassID.GHOST:
            return {"type": "identify", "class_name": "Ghost", "name": "A spectral presence."}
        if obj.class_id == ClassID.HOUSE_CAT:
            return {"type": "identify", "class_name": "House Cat", "name": "A fluffy companion."}
        if obj.class_id == ClassID.BUREAUCRAT:
            return {"type": "identify", "class_name": "Bureaucrat", "name": "An official-looking person."}
        return {"type": "identify", "class_name": "Creature", "name": ""}

    async def handle_DO(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID

        if obj.class_id == ClassID.GHOST:
            msg = random.choice(GHOST_MESSAGES)
            await region.broadcast_all({"type": "SPEAK", "name": "Ghost", "text": msg})
            # Ghost might attack
            if random.random() < 0.3:
                avatar_noid = args.get("avatar_noid")
                avatar = region.get_avatar(avatar_noid)
                if avatar:
                    damage = random.randint(5, 15)
                    avatar.health = max(0, avatar.health - damage)
                    return {"type": "ACTION_RESULT", "text": f"The ghost attacks! (-{damage} HP)"}
            return {"type": "ACTION_RESULT", "text": msg}

        if obj.class_id == ClassID.HOUSE_CAT:
            action = random.choice(CAT_ACTIONS)
            await region.broadcast_all({"type": "SPEAK", "name": "Cat", "text": "Meow!"})
            return {"type": "ACTION_RESULT", "text": action}

        if obj.class_id == ClassID.BUREAUCRAT:
            response = random.choice(BUREAUCRAT_RESPONSES)
            await region.broadcast_all({"type": "SPEAK", "name": "Bureaucrat", "text": response})
            return {"type": "ACTION_RESULT", "text": response}

        return {"type": "ACTION_RESULT", "text": "The creature looks at you."}

    async def handle_GRAB(self, region, noid, args):
        obj = region.get_object(noid)
        if not obj:
            return {"success": False, "error": "not found"}
        from ..models import ClassID
        if obj.class_id == ClassID.HOUSE_CAT:
            avatar_noid = args.get("avatar_noid")
            obj.container_noid = avatar_noid
            await region.broadcast_all({"type": "GRAB", "noid": avatar_noid, "target": noid})
            return {"success": True}
        return {"type": "ACTION_RESULT", "text": "You can't pick that up."}
