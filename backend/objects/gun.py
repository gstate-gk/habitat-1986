"""Gun. From class_gun.pl1

The original gun has no ammo and no per-gun damage: ATTACK goes through
generic_ATTACK (actions_weapon.incl.pl1, flat 20 damage). That action lives in
original_actions.py; this handler only supplies the class name."""
from .base import BaseObject


class GunHandler(BaseObject):
    class_name = "gun"
