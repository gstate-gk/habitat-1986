"""
Shared helper routines.
Converted from: helpers.pl1 (kill_avatar, spend, pay_to, holding, adjacent)
and actions_weapon.incl.pl1 (damage_avatar, damage_object).

Web-model note: the original keeps money as a CLASS_TOKENS object in the
avatar's HANDS slot. The web version keeps it as Avatar.tokens_in_hand
(an integer). spend/pay_to operate on that integer; this is a recorded
simplification, not a behavior change.
"""
from __future__ import annotations

from .models import Avatar, GameObject

# actions_weapon.incl.pl1
MISS = 0
DESTROY = 1
HIT = 2
DEATH = 3

# class_table / helpers.pl1 kill_avatar: respawn position and bank penalty
RESPAWN_X = 80
RESPAWN_Y = 132
DEATH_BANK_FACTOR = 0.8
WEAPON_DAMAGE = 20          # damage_avatar: "just subtract 20 points"
TEXT_LENGTH = 114


def test_bit(value: int, bit: int) -> bool:
    """Bit n is 2**n (LSB 0). Assumption about the PL/I test_bit numbering."""
    return bool(value & (1 << bit))


def set_bit(value: int, bit: int) -> int:
    return value | (1 << bit)


def clear_bit(value: int, bit: int) -> int:
    return value & ~(1 << bit)


def holding(obj: GameObject | None, avatar: Avatar | None) -> bool:
    """helpers.pl1 holding: object.container = avatar.noid."""
    return bool(obj and avatar and obj.container_noid == avatar.noid)


def adjacent(*_args, **_kwargs) -> bool:
    """width.pl1 adjacent: with ADJACENCY_ON off it calls old_adjacent,
    which returns true. The image-geometry tables of the C64 client are not
    part of the web version, so the old_adjacent behavior is used."""
    return True


def spend(avatar: Avatar, amount: int) -> bool:
    """helpers.pl1 spend: pay from the tokens in hand."""
    if amount < 0 or avatar.tokens_in_hand < amount:
        return False
    avatar.tokens_in_hand -= amount
    return True


def pay_to(avatar: Avatar, amount: int) -> bool:
    """helpers.pl1 pay_to: put tokens into the avatar's hand."""
    if amount < 0:
        return False
    avatar.tokens_in_hand += amount
    return True


def damage_avatar(who: Avatar) -> int:
    """actions_weapon.incl.pl1 damage_avatar.
    health <= 0 -> HIT (no change); health <= 20 -> DEATH (health -= 20);
    otherwise HIT (health -= 20)."""
    if who.health <= 0:
        return HIT
    if who.health <= WEAPON_DAMAGE:
        who.health -= WEAPON_DAMAGE
        return DEATH
    who.health -= WEAPON_DAMAGE
    return HIT


def kill_avatar(region, victim: Avatar) -> None:
    """helpers.pl1 kill_avatar (web subset).

    Drops whatever is in the hands to the ground, resets position and
    health, takes 20% of the bank balance, clears stun, counts the death
    and zeroes the per-life statistics.
    The original then auto_teleports the avatar to its turf; the web version
    respawns in the current region (recorded as a simplification)."""
    for obj in list(region.objects.values()):
        if obj.container_noid == victim.noid:
            obj.container_noid = 0
            obj.x = victim.x
            obj.y = victim.y
    victim.x = RESPAWN_X
    victim.y = RESPAWN_Y
    victim.health = 255
    victim.bank_account = int(float(victim.bank_account) * DEATH_BANK_FACTOR)
    victim.stun_count = 0
    victim.deaths += 1
    victim.travel = 0
    victim.teleports = 0
    victim.kills = 0


def result(success: bool, text: str = "", **extra) -> dict:
    """Common reply shape (the original's r_msg_1 / r_msg_s)."""
    out = {"type": "ACTION_RESULT", "success": bool(success), "text": text}
    out.update(extra)
    return out
