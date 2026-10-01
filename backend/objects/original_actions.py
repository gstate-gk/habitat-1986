"""
Class-specific actions converted one-to-one from the original class_*.pl1
action tables (Class_Table(I).actions->a(N) = xxx_ACTION).

Each function has the shape  async f(region, obj, avatar, args) -> dict
and is registered in CLASS_ACTIONS under (ClassID, "ACTION").

The web client sends a single generic DO for an object's main action.
PRIMARY_DO maps DO to the original action of that class (a UI adaptation,
not part of the original protocol).

Web-model substitutions (recorded in GAP_ANALYSIS.md):
  * tokens in hand are Avatar.tokens_in_hand, not a CLASS_TOKENS object
  * "contents" of a container are region objects whose container_noid
    equals the container's noid
  * adjacent() is old_adjacent (always true); see helpers.adjacent
  * state fields of an object live in obj.extra
"""
from __future__ import annotations

import random
from typing import Awaitable, Callable

from ..models import ClassID, Posture
from ..fortunes_data import FORTUNES, LAST_MSG
from ..helpers import (
    DEATH, DESTROY, HIT, MISS,
    adjacent, clear_bit, damage_avatar, holding, kill_avatar, pay_to,
    result, set_bit, spend, test_bit,
)

ActionFn = Callable[..., Awaitable[dict]]
CLASS_ACTIONS: dict[tuple[int, str], ActionFn] = {}
PRIMARY_DO: dict[int, str | Callable] = {}

COKE_COST = 5            # class_coke_machine.pl1 COKE_COST
FORTUNE_COST = 2         # class_fortune_machine.pl1 FORTUNE_COST
GRENADE_FUSE_DELAY = 20  # class_grenade.pl1 (seconds)
GENIE_TIMEOUT = 30       # class_magic_lamp.pl1 (seconds)
SIT_GROUND = 132
GET_SHOT_POSTURE = 138
OPERATE = 152

MAGIC_LAMP_WAITING = 0
MAGIC_LAMP_GENIE = 1


def action(class_id: int, name: str):
    def deco(fn):
        CLASS_ACTIONS[(int(class_id), name)] = fn
        return fn
    return deco


async def say(region, name: str, text: str):
    """helpers.pl1 object_say / object_broadcast."""
    await region.broadcast_all({"type": "SPEAK", "name": name, "text": text})


def _other_avatar(region, avatar):
    """Web adaptation: the client sends no target id with DO, so the
    nearest other avatar is used when args has no 'target'."""
    best, best_d = None, None
    for av in region.avatars.values():
        if av.noid == avatar.noid:
            continue
        d = abs(av.x - avatar.x) + abs(av.y - avatar.y)
        if best is None or d < best_d:
            best, best_d = av, d
    return best


# --- coke_machine / fortune_machine / pawn_machine ---

@action(ClassID.COKE_MACHINE, "PAY")
async def coke_machine_PAY(region, obj, avatar, args):
    if spend(avatar, COKE_COST):
        obj.extra["take"] = obj.extra.get("take", 0) + COKE_COST
        await region.broadcast_all({"type": "PAY", "noid": avatar.noid,
                                    "target": obj.noid, "amount": COKE_COST})
        await region.broadcast_all({"type": "POSTURE", "noid": avatar.noid,
                                    "posture": OPERATE})
        return result(True, "", amount=COKE_COST, tokens=avatar.tokens_in_hand)
    text = f"You don't have enough money.  A Choke costs ${COKE_COST}."
    await say(region, "Coke Machine", text)
    return result(False, text, amount=COKE_COST)


@action(ClassID.FORTUNE_MACHINE, "PAY")
async def fortune_machine_PAY(region, obj, avatar, args):
    if spend(avatar, FORTUNE_COST):
        text = FORTUNES[random.randint(0, LAST_MSG)]
        await region.broadcast_all({"type": "PAY", "noid": avatar.noid,
                                    "target": obj.noid, "amount": FORTUNE_COST})
        await say(region, "Fortune Machine", text)
        obj.extra["take"] = obj.extra.get("take", 0) + FORTUNE_COST
        return result(True, text, amount=FORTUNE_COST, tokens=avatar.tokens_in_hand)
    text = f"You don't have enough money.  Fortunes cost ${FORTUNE_COST}."
    return result(False, text, amount=FORTUNE_COST)


@action(ClassID.PAWN_MACHINE, "MUNCH")
async def pawn_machine_MUNCH(region, obj, avatar, args):
    contents = [o for o in region.objects.values() if o.container_noid == obj.noid]
    if adjacent(obj) and contents:
        item = contents[0]
        # item_value() is not in the available source; the web version reads
        # obj.extra["value"] (0 when absent).
        if pay_to(avatar, int(item.extra.get("value", 0))):
            await region.broadcast_all({"type": "MUNCH", "noid": obj.noid,
                                        "avatar": avatar.noid})
            region.remove_object(item.noid)
            return result(True)
    return result(False)


PRIMARY_DO[ClassID.COKE_MACHINE] = "PAY"
PRIMARY_DO[ClassID.FORTUNE_MACHINE] = "PAY"
PRIMARY_DO[ClassID.PAWN_MACHINE] = "MUNCH"


# --- changomatic / sex_changer ---

def _changeable(region, target) -> bool:
    """changomatic.pl1 changeable: not an avatar, and the class has no GET
    action (scenery). The web registry marks scenery with StaticHandler."""
    from .base import OBJECT_REGISTRY
    if target.class_id == ClassID.AVATAR:
        return False
    handler = OBJECT_REGISTRY.get(target.class_id)
    return handler is None or type(handler).__name__ == "StaticHandler"


@action(ClassID.CHANGOMATIC, "CHANGE")
async def changomatic_CHANGE(region, obj, avatar, args):
    target = region.objects.get(args.get("target", -1))
    own_turf = region.region.region_id == avatar.turf_region and avatar.turf_region != 0
    if target is None or not (own_turf and _changeable(region, target)):
        await say(region, "Changomatic", "You can't change that here.")
        return result(False, "You can't change that here.")
    o = target.orientation
    while True:
        o += 8
        if not test_bit(o, 3):
            o = clear_bit(o, 8)
        o = clear_bit(o, 9)
        if o // 8 != 15:
            break
    target.orientation = o
    await region.broadcast_all({"type": "CHANGE", "noid": obj.noid,
                                "target": target.noid, "orientation": o})
    return result(True, "", orientation=o)


PRIMARY_DO[ClassID.CHANGOMATIC] = "CHANGE"


@action(ClassID.SEX_CHANGER, "SEXCHANGE")
async def sex_changer_SEXCHANGE(region, obj, avatar, args):
    if adjacent(obj):
        if test_bit(avatar.orientation, 8):
            avatar.orientation = clear_bit(avatar.orientation, 8)
        else:
            avatar.orientation = set_bit(avatar.orientation, 8)
        await region.broadcast_all({"type": "SEXCHANGE", "noid": avatar.noid,
                                    "orientation": avatar.orientation})
    return result(True)


PRIMARY_DO[ClassID.SEX_CHANGER] = "SEXCHANGE"


# --- die / game_piece / compass ---

@action(ClassID.DIE, "ROLL")
async def die_ROLL(region, obj, avatar, args):
    obj.gr_state = random.randint(0, 5)   # self.gr_state = random(6)
    await region.broadcast_all({"type": "ROLL", "noid": obj.noid,
                                "gr_state": obj.gr_state})
    return result(True, "", gr_state=obj.gr_state)


PRIMARY_DO[ClassID.DIE] = "ROLL"

CHECKER_PIECE = 6
CHECKER_KING = 7


@action(ClassID.GAME_PIECE, "ROLL")
async def game_piece_CHANGE(region, obj, avatar, args):
    if obj.gr_state == CHECKER_PIECE:
        obj.gr_state = CHECKER_KING
    elif obj.gr_state == CHECKER_KING:
        obj.gr_state = CHECKER_PIECE
    await region.broadcast_all({"type": "ROLL", "noid": obj.noid,
                                "gr_state": obj.gr_state})
    return result(True, "", gr_state=obj.gr_state)


PRIMARY_DO[ClassID.GAME_PIECE] = "ROLL"

# compass_DIRECT: byte(124)/(126)/(125)/(127) for gr_state 0..3
_COMPASS_BYTES = {0: 124, 1: 126, 2: 125, 3: 127}


@action(ClassID.COMPASS, "DIRECT")
async def compass_DIRECT(region, obj, avatar, args):
    code = _COMPASS_BYTES.get(obj.gr_state)
    text = "WEST: " + (chr(code) if code is not None else "?")
    return result(True, text, direction_code=code)


PRIMARY_DO[ClassID.COMPASS] = "DIRECT"


# --- drugs ---

NUMBER_OF_DRUG_EFFECTS = 3
DRUG_HELP = {
    1: "Healing pills: good for what ails you.",
    2: "DANGER!!  POISON!!",
    3: "Darkening tablets.",
}


@action(ClassID.DRUGS, "TAKE")
async def drugs_TAKE(region, obj, avatar, args):
    effect = obj.extra.get("effect", 1)
    count = obj.extra.get("count", 1)
    if effect < 1 or effect > NUMBER_OF_DRUG_EFFECTS:
        return result(False)
    if holding(obj, avatar) and count > 0:
        obj.extra["count"] = count = count - 1
        await region.broadcast_all({"type": "TAKE", "noid": obj.noid,
                                    "avatar": avatar.noid})
        if count <= 0:
            await say(region, "Drugs", "All gone!")
        if effect == 1:                       # heal_avatar
            avatar.health = 255
            await say(region, avatar.name, "I feel much better now.")
        elif effect == 2:                     # poison_avatar
            await say(region, avatar.name, "I feel very sick.")
            kill_avatar(region, avatar)
        else:                                 # turn_avatar_black
            await say(region, avatar.name, "I feel very odd.")
            avatar.customize = [17, 17]
            for head in region.objects.values():
                if head.class_id == ClassID.HEAD and head.container_noid == avatar.noid:
                    head.orientation = (head.orientation & 0x87) | 0x08
        if count <= 0:
            region.remove_object(obj.noid)
        return result(True, "", effect=effect)
    return result(False)


@action(ClassID.DRUGS, "HELP")
async def drugs_HELP(region, obj, avatar, args):
    effect = obj.extra.get("effect", 1)
    if effect < 1 or effect > NUMBER_OF_DRUG_EFFECTS:
        return {"type": "identify", "class_name": "Drugs",
                "name": "Illegible Latin scrawl."}
    count = obj.extra.get("count", 1)
    return {"type": "identify", "class_name": "Drugs",
            "name": (f"DRUGS: select DO to consume.  This pill bottle has {count} "
                     f"pills remaining.  This bottle contains: {DRUG_HELP[effect]}")}


PRIMARY_DO[ClassID.DRUGS] = "TAKE"


# --- spray_can / shovel / windup_toy / bottle ---

LEG_LIMB, TORSO_LIMB, ARM_LIMB, FACE_LIMB = 0, 1, 2, 3


@action(ClassID.SPRAY_CAN, "SPRAY")
async def spray_can_SPRAY(region, obj, avatar, args):
    limb = args.get("limb", TORSO_LIMB)
    success = False
    if holding(obj, avatar):
        pattern = obj.orientation & 0x0078
        if limb == TORSO_LIMB:
            success = True
            avatar.customize[0] = (avatar.customize[0] & 0x00F0) | (pattern // 8)
        elif limb == LEG_LIMB:
            success = True
            avatar.customize[0] = (avatar.customize[0] & 0x000F) | (pattern * 2)
        elif limb == ARM_LIMB:
            success = True
            avatar.customize[1] = (avatar.customize[1] & 0x000F) | (pattern * 2)
        elif limb == FACE_LIMB:
            for head in region.objects.values():
                if head.class_id == ClassID.HEAD and head.container_noid == avatar.noid:
                    head.orientation = (head.orientation & 0x0087) | pattern
                    success = True
                    break
    if success:
        await region.broadcast_all({"type": "SPRAY", "noid": obj.noid,
                                    "avatar": avatar.noid,
                                    "customize": list(avatar.customize)})
        # struct_spray_can charge initial value comes from region data; the
        # web default is 10.
        charge = obj.extra.get("charge", 10) - 1
        obj.extra["charge"] = charge
        if charge <= 0:
            await say(region, "Spray Can", "This sprayer has run out.")
            region.remove_object(obj.noid)
    return result(success, "", customize=list(avatar.customize))


PRIMARY_DO[ClassID.SPRAY_CAN] = "SPRAY"


@action(ClassID.SHOVEL, "DIG")
async def shovel_DIG(region, obj, avatar, args):
    if holding(obj, avatar):
        await region.broadcast_all({"type": "DIG", "noid": obj.noid,
                                    "avatar": avatar.noid})
    return result(True)


PRIMARY_DO[ClassID.SHOVEL] = "DIG"


@action(ClassID.WINDUP_TOY, "WIND")
async def windup_toy_WIND(region, obj, avatar, args):
    if holding(obj, avatar):
        level = min(obj.extra.get("wind_level", 0) + 1, 4)
        obj.extra["wind_level"] = level
        obj.gr_state = 1
        await region.broadcast_all({"type": "WIND", "noid": obj.noid})
    return result(True)


PRIMARY_DO[ClassID.WINDUP_TOY] = "WIND"


@action(ClassID.BOTTLE, "FILL")
async def bottle_FILL(region, obj, avatar, args):
    # helpers.pl1 at_water: "return(true); /* For now */"
    ok = holding(obj, avatar) and not obj.extra.get("filled", False)
    if ok:
        obj.extra["filled"] = True
        obj.gr_state = 1
        await region.broadcast_all({"type": "FILL", "noid": obj.noid,
                                    "avatar": avatar.noid})
    return result(ok)


@action(ClassID.BOTTLE, "POUR")
async def bottle_POUR(region, obj, avatar, args):
    ok = holding(obj, avatar) and obj.extra.get("filled", False)
    if ok:
        obj.extra["filled"] = False
        obj.gr_state = 0
        await region.broadcast_all({"type": "POUR", "noid": obj.noid,
                                    "avatar": avatar.noid})
    return result(ok)


PRIMARY_DO[ClassID.BOTTLE] = lambda obj: "POUR" if obj.extra.get("filled") else "FILL"


# --- weapons: generic_ATTACK, fake_gun, stun_gun, grenade ---

@action(ClassID.KNIFE, "ATTACK")
@action(ClassID.CLUB, "ATTACK")
@action(ClassID.GUN, "ATTACK")
async def generic_ATTACK(region, obj, avatar, args):
    """actions_weapon.incl.pl1 generic_ATTACK. Damage is the original's flat
    20 (see helpers.damage_avatar); only a mailbox is damageable."""
    target_id = args.get("target")
    if target_id is None:
        near = _other_avatar(region, avatar)        # web adaptation
        target_id = near.noid if near else None
    target_av = region.avatars.get(target_id)
    target_obj = region.objects.get(target_id)
    if target_av is None and target_obj is None:
        return result(False, "", outcome=MISS, target=target_id)

    success = MISS
    if avatar.stun_count > 0:
        await say(region, avatar.name, "I can't attack.  I am stunned.")
    elif getattr(region.region, "weapons_free", False):
        await say(region, "Weapon",
                  "This is a weapons-free zone.  Your weapon will not operate here.")
    elif adjacent(obj) or obj.class_id == ClassID.GUN:   # is_ranged_weapon
        if target_obj is not None and target_obj.class_id == ClassID.HEAD \
                and target_obj.container_noid in region.avatars:
            target_av = region.avatars[target_obj.container_noid]
            target_id = target_av.noid
            target_obj = None
        if target_av is not None:
            success = damage_avatar(target_av)
            target_av.activity = SIT_GROUND
            await region.broadcast_all({"type": "ATTACK", "noid": avatar.noid,
                                        "target": target_id, "success": success})
            await region.broadcast_all({"type": "GUN_SHOT", "shooter": avatar.noid,
                                        "target_noid": target_id, "damage": 20})
        else:
            if target_obj.class_id == ClassID.MAILBOX:   # damageable()
                success = DESTROY
                region.remove_object(target_obj.noid)
            await region.broadcast_all({"type": "BASH", "noid": avatar.noid,
                                        "target": target_id, "success": success})
    # Important not to kill avatar before response message goes out!
    reply = result(success != MISS, "", outcome=success, target=target_id)
    if success == DEATH and target_av is not None:
        kill_avatar(region, target_av)
        avatar.kills += 1
        await region.broadcast_all({"type": "AVATAR_DEATH", "noid": target_id,
                                    "name": target_av.name})
    return reply


for _cid in (ClassID.KNIFE, ClassID.CLUB, ClassID.GUN):
    PRIMARY_DO[_cid] = "ATTACK"


@action(ClassID.STUN_GUN, "STUN")
async def stun_gun_STUN(region, obj, avatar, args):
    target_id = args.get("target")
    if target_id is None:
        near = _other_avatar(region, avatar)        # web adaptation
        target_id = near.noid if near else None
    target = region.avatars.get(target_id)
    if holding(obj, avatar) and target is not None:
        target.stun_count = 3
        await region.broadcast_all({"type": "ATTACK", "noid": avatar.noid,
                                    "target": target_id, "success": 0})
        return result(True)
    return result(False)


PRIMARY_DO[ClassID.STUN_GUN] = "STUN"

FAKE_GUN_READY = 0
FAKE_GUN_FIRED = 1


@action(ClassID.FAKE_GUN, "FAKESHOOT")
async def fake_gun_FAKESHOOT(region, obj, avatar, args):
    state = obj.extra.get("state", FAKE_GUN_READY)
    if holding(obj, avatar) and state == FAKE_GUN_READY:
        obj.extra["state"] = obj.gr_state = FAKE_GUN_FIRED
        await region.broadcast_all({"type": "FAKESHOOT", "noid": obj.noid})
        return result(True)
    return result(False)


@action(ClassID.FAKE_GUN, "RESET")
async def fake_gun_RESET(region, obj, avatar, args):
    state = obj.extra.get("state", FAKE_GUN_READY)
    if holding(obj, avatar) and state == FAKE_GUN_FIRED:
        obj.extra["state"] = obj.gr_state = FAKE_GUN_READY
        await region.broadcast_all({"type": "RESET", "noid": obj.noid})
        return result(True)
    return result(False)


PRIMARY_DO[ClassID.FAKE_GUN] = lambda obj: (
    "RESET" if obj.extra.get("state", FAKE_GUN_READY) == FAKE_GUN_FIRED else "FAKESHOOT")


@action(ClassID.GRENADE, "PULLPIN")
async def grenade_PULLPIN(region, obj, avatar, args):
    if getattr(region.region, "weapons_free", False):
        await say(region, "Grenade",
                  "This is a weapons-free zone.  Your grenade will not operate here.")
        return result(False)
    if holding(obj, avatar) and not obj.extra.get("pinpulled", False):
        obj.extra["pinpulled"] = True
        await say(region, "Grenade", "Sproing!!!")
        region.tact(GRENADE_FUSE_DELAY, grenade_explosion, obj.noid)
        return result(True)
    return result(False)


async def grenade_explosion(region, grenade_noid: int):
    """Grenade_Explosion (Tact callback): destroy the grenade and damage
    every avatar in the region."""
    obj = region.objects.get(grenade_noid)
    if obj is None or obj.class_id != ClassID.GRENADE:
        return
    await region.broadcast_all({"type": "EXPLODE", "noid": grenade_noid})
    region.remove_object(grenade_noid)
    for target in list(region.avatars.values()):
        res = damage_avatar(target)
        if res > 0:
            target.activity = SIT_GROUND
            await region.broadcast_all({"type": "POSTURE", "noid": target.noid,
                                        "posture": GET_SHOT_POSTURE})
            await region.broadcast_all({"type": "GUN_SHOT", "shooter": grenade_noid,
                                        "target_noid": target.noid, "damage": 20})
            if res == DEATH:
                kill_avatar(region, target)
                await region.broadcast_all({"type": "AVATAR_DEATH",
                                            "noid": target.noid,
                                            "name": target.name})


PRIMARY_DO[ClassID.GRENADE] = "PULLPIN"


@action(ClassID.GRENADE, "HELP")
async def grenade_HELP(region, obj, avatar, args):
    if not obj.extra.get("pinpulled", False):
        text = ("Grenade: Select DO (while holding) to pull pin, then throw to "
                "ground and leave the region quickly.")
    else:
        text = "Grenade: Pin pulled!  Run away now!!!"
    return {"type": "identify", "class_name": "Grenade", "name": text}


@action(ClassID.BOOMERANG, "THROW")
async def boomerang_THROW(region, obj, avatar, args):
    """boomerang_THROW: the object leaves the world and Boomerang_Return is
    scheduled through schedule_event. helpers.pl1 schedule_event is a stub
    ('unimplemented proc'), so the original never returns the boomerang.
    The web version schedules the return (intentional change, recorded)."""
    if holding(obj, avatar):
        thrower = avatar.noid
        await region.broadcast_all({"type": "THROWAWAY", "noid": obj.noid})
        obj.container_noid = -1          # disappear_object
        region.tact(random.randint(10, 30), boomerang_return, obj.noid, thrower)
        return result(True)
    return result(False)


async def boomerang_return(region, boomerang_noid: int, thrower_noid: int):
    obj = region.objects.get(boomerang_noid)
    whom = region.avatars.get(thrower_noid)
    if obj is None:
        return
    held = any(o.container_noid == thrower_noid for o in region.objects.values())
    if whom is not None and not held:
        obj.container_noid = thrower_noid
        await region.broadcast_all({"type": "RETURN", "noid": boomerang_noid,
                                    "avatar": thrower_noid})
        return
    region.tact(random.randint(10, 30), boomerang_return, boomerang_noid, thrower_noid)


PRIMARY_DO[ClassID.BOOMERANG] = "THROW"


# --- garbage_can / hole-less containers ---

@action(ClassID.GARBAGE_CAN, "FLUSH")
async def garbage_can_FLUSH(region, obj, avatar, args):
    for o in [o for o in region.objects.values() if o.container_noid == obj.noid]:
        region.remove_object(o.noid)
    await region.broadcast_all({"type": "FLUSH", "noid": obj.noid})
    return result(True)


# --- magic_lamp: RUB / WISH with 30 s genie timeout ---

@action(ClassID.MAGIC_LAMP, "RUB")
async def magic_lamp_RUB(region, obj, avatar, args):
    state = obj.extra.get("lamp_state", MAGIC_LAMP_WAITING)
    if holding(obj, avatar) and state == MAGIC_LAMP_WAITING:
        obj.extra["lamp_state"] = obj.gr_state = MAGIC_LAMP_GENIE
        obj.extra["wisher"] = avatar.noid
        obj.extra["genie_stage"] = 2
        obj.extra["_timeout"] = region.tact(GENIE_TIMEOUT, genie_gets_impatient, obj.noid)
        speech = f"Oh, Master {avatar.name}, your wish is my command!"
        await region.broadcast_all({"type": "RUB", "noid": obj.noid, "text": speech})
        return result(True, speech)
    return result(False, "")


@action(ClassID.MAGIC_LAMP, "WISH")
async def magic_lamp_WISH(region, obj, avatar, args):
    wish = str(args.get("text", ""))
    await region.broadcast_all({"type": "SPEAK", "noid": avatar.noid,
                                "name": avatar.name, "text": wish})
    if obj.extra.get("wisher") == avatar.noid:
        region.clear_tact(obj.extra.pop("_timeout", None))
        # message_to_god is not in the available source; the wish is logged.
        print(f"WISH from {avatar.name}: {wish}")
        await region.broadcast_all({"type": "WISH", "noid": obj.noid,
                                    "text": "Well, I'll see what I can do."})
        region.remove_object(obj.noid)
        return result(True, "Well, I'll see what I can do.")
    await say(region, "Magic Lamp", "Buzz off creep!  It's not *your* wish.")
    return result(False, "Buzz off creep!  It's not *your* wish.")


async def genie_gets_impatient(region, lamp_noid: int):
    obj = region.objects.get(lamp_noid)
    if obj is None or obj.class_id != ClassID.MAGIC_LAMP:
        return
    if obj.extra.get("genie_stage") == 2:
        await say(region, "Genie", "Come on now, I don't have all day!")
        obj.extra["genie_stage"] = 3
        obj.extra["_timeout"] = region.tact(GENIE_TIMEOUT, genie_gets_impatient, lamp_noid)
        return
    await region.broadcast_all({
        "type": "WISH", "noid": lamp_noid,
        "text": "Sorry, I just don't have time for indecisiveness!"})
    region.remove_object(lamp_noid)


PRIMARY_DO[ClassID.MAGIC_LAMP] = lambda obj: (
    "RUB" if obj.extra.get("lamp_state", MAGIC_LAMP_WAITING) == MAGIC_LAMP_WAITING else "WISH")


# --- tokens SPLIT, escape_dev, aquarium, tape, matchbook, sensor ---

@action(ClassID.TOKENS, "SPLIT")
async def tokens_SPLIT(region, obj, avatar, args):
    """tokens_SPLIT: shrink this token to `amount`, put the remainder into
    another token in the pocket (or a new token)."""
    amount = int(args.get("amount", 0))
    total = obj.extra.get("denomination", 0)
    if amount >= total or amount <= 0:
        return result(False)
    rest = total - amount
    pocket = [o for o in region.objects.values()
              if o.class_id == ClassID.TOKENS and o.container_noid == avatar.noid
              and o.noid != obj.noid]
    if pocket:
        big = pocket[0].extra.get("denomination", 0) + rest
        if big > 65536:
            return result(False)
        pocket[0].extra["denomination"] = big
    else:
        if rest > 65536:
            return result(False)
        from ..models import GameObject
        region.add_object(GameObject(class_id=ClassID.TOKENS,
                                     container_noid=avatar.noid,
                                     extra={"denomination": rest}))
    obj.extra["denomination"] = amount
    return result(True)


@action(ClassID.ESCAPE_DEV, "BUGOUT")
async def escape_dev_BUGOUT(region, obj, avatar, args):
    charge = obj.extra.get("charge", 1)
    if holding(obj, avatar) and charge > 0:
        if avatar.turf_region == region.region.region_id:
            await say(region, "Escape Device", "You're already home.")
            return result(False, "You're already home.")
        if avatar.turf_region == 0:
            return result(False, "You have no turf to escape to.")
        avatar.x, avatar.y = 80, 132
        obj.extra["charge"] = charge - 1
        return {"type": "region_change", "success": True,
                "destination": avatar.turf_region}
    await say(region, "Escape Device", "Its charge is all used up.")
    return result(False, "Its charge is all used up.")


PRIMARY_DO[ClassID.ESCAPE_DEV] = "BUGOUT"

FISH_SWIMMING = 1
FISH_FEEDING = 2


@action(ClassID.AQUARIUM, "FEED")
async def aquarium_FEED(region, obj, avatar, args):
    """aquarium_FEED. Fish_Fed/Fish_Die are scheduled with schedule_event,
    a stub in helpers.pl1, so the original never leaves the FEEDING state;
    the same is true here."""
    state = obj.extra.get("state", FISH_SWIMMING)
    food = any(o.class_id == ClassID.INSTANT_OBJECT and o.container_noid == avatar.noid
               for o in region.objects.values())
    if food and state == FISH_SWIMMING:
        obj.extra["state"] = obj.gr_state = FISH_FEEDING
        await region.broadcast_all({"type": "CHANGESTATE", "noid": obj.noid,
                                    "state": FISH_FEEDING})
    return result(True)


PRIMARY_DO[ClassID.AQUARIUM] = "FEED"


@action(ClassID.MATCHBOOK, "README")
async def matchbook_README(region, obj, avatar, args):
    text = obj.extra.get("text", "") if holding(obj, avatar) else ""
    return result(True, text)


PRIMARY_DO[ClassID.MATCHBOOK] = "README"


@action(ClassID.TAPE, "READLABEL")
async def tape_READLABEL(region, obj, avatar, args):
    text = obj.extra.get("title", "") if holding(obj, avatar) else ""
    return result(True, text)


PRIMARY_DO[ClassID.TAPE] = "READLABEL"


@action(ClassID.SENSOR, "SCAN")
async def sensor_SCAN(region, obj, avatar, args):
    """sensor_SCAN, scan type 1 = sense_weapons."""
    if not holding(obj, avatar):
        return result(False)
    scan_type = obj.extra.get("scan_type", 1)
    if scan_type != 1:
        await say(region, "Sensor", "This sensor is broken.")
        return result(False, "This sensor is broken.")
    weapons = (ClassID.GUN, ClassID.KNIFE, ClassID.CLUB, ClassID.GRENADE)
    found = any(o.class_id in weapons for o in region.objects.values())
    obj.gr_state = 1 if found else 0
    await region.broadcast_all({"type": "SCAN", "noid": obj.noid,
                                "result": obj.gr_state})
    return result(found, "", gr_state=obj.gr_state)


PRIMARY_DO[ClassID.SENSOR] = "SCAN"


def resolve_primary(class_id: int, obj) -> str | None:
    p = PRIMARY_DO.get(class_id)
    if callable(p):
        return p(obj)
    return p
