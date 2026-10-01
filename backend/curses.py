"""
Avatar curses. Converted from: curses.pl1 (curse_touch, activate_head_curse).

Web-model substitution: the web version has no CLASS_HEAD object per avatar,
so Avatar.style stands in for head.style (recorded in GAP_ANALYSIS.md).
The original "headless avatars are immune" rule is therefore not modelled.
"""
from __future__ import annotations

from .models import Avatar, CurseType

HEAD_COOTIE = 117
HEAD_SMILEY = 110
HEAD_MUTANT = 27
HEAD_FLY = 13
CURSE_IMMUNITY_BIT = 32

# curse_counter initial values from activate_head_curse
_COUNTER = {
    CurseType.COOTIES: 1,      # just moves around
    CurseType.SMILEY: 2,       # exponential explosion
    CurseType.MUTANT: 32767,   # virtually infinite
    CurseType.FLY: 0,          # doesn't spread
}
_STYLE = {
    CurseType.COOTIES: HEAD_COOTIE,
    CurseType.SMILEY: HEAD_SMILEY,
    CurseType.MUTANT: HEAD_MUTANT,
    CurseType.FLY: HEAD_FLY,
}


def activate_head_curse(victim: Avatar, curse_type: int) -> bool:
    if victim.curse_type == curse_type:
        return False
    if victim.curse_type == CurseType.NONE:
        victim.true_head_style = victim.style
    victim.curse_type = curse_type
    if curse_type == CurseType.NONE:
        victim.style = victim.true_head_style
        victim.curse_counter = 0
        victim.curse_immune = True          # nitty_bits(CURSE_IMMUNITY_BIT)
    else:
        victim.style = _STYLE[CurseType(curse_type)]
        victim.curse_counter = _COUNTER[CurseType(curse_type)]
    return True


def curse_touch(curser: Avatar, cursee: Avatar) -> None:
    if cursee.curse_type != CurseType.NONE:
        return
    if curser.curse_type in (CurseType.COOTIES, CurseType.SMILEY, CurseType.MUTANT):
        if cursee.curse_immune:
            return
        if not activate_head_curse(cursee, curser.curse_type):
            return
        curser.curse_counter -= 1
        if curser.curse_counter <= 0:
            activate_head_curse(curser, CurseType.NONE)


def buzzify(text: str) -> str:
    """class_avatar.pl1 buzzify: letters -> z/Z, digits -> z, then the first
    character of every z-run becomes b/B."""
    out = []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            out.append("Z" if ch.isupper() else "z")
        elif ch.isascii() and ch.isdigit():
            out.append("z")
        else:
            out.append(ch)
    for i in range(len(out) - 1, -1, -1):
        prev_not_z = i == 0 or out[i - 1] not in "zZ"
        if prev_not_z and out[i] in "zZ":
            out[i] = "b" if out[i] == "z" else "B"
    return "".join(out)
