"""
Habitat data models.
Converted from PL/I BASED structures and %include definitions.

Original: struct_gen_object, struct_avatar, struct_class, region.structs.incl.pl1
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# --- PL/I %replace constants → Python IntEnum ---

class Action(IntEnum):
    HELP = 0
    GO = 1
    DO = 2
    GRAB = 4
    HAND = 5
    POSTURE = 6
    SPEAK = 7
    WALK = 8
    PUT = 9
    THROW = 10
    MAGIC = 13
    PAY = 11
    CLOSE = 14
    OPEN = 15


class ClassID(IntEnum):
    REGION = 0
    AVATAR = 1
    AMULET = 2
    GHOST = 3
    ATM = 4
    GAME_PIECE = 5
    BAG = 6
    BALL = 7
    BOOK = 10
    BOOMERANG = 11
    BOTTLE = 12
    BOX = 13
    CLUB = 16
    COMPASS = 17
    COUNTERTOP = 18
    CRYSTAL_BALL = 20
    DIE = 21
    DISPLAY_CASE = 22
    DOOR = 23
    DROPBOX = 24
    DRUGS = 25
    ESCAPE_DEV = 26
    FAKE_GUN = 27
    ELEVATOR = 28
    FLAG = 29
    FLASHLIGHT = 30
    FRISBEE = 31
    GARBAGE_CAN = 32
    GROUND = 33
    GUN = 34
    GRENADE = 35
    HAND_OF_GOD = 38
    HAT = 39
    INSTANT_OBJECT = 40
    JACKET = 41
    KEY = 42
    KNICK_KNACK = 43
    KNIFE = 44
    MAGIC_LAMP = 45
    MAGIC_STAFF = 46
    MAGIC_WAND = 47
    MAILBOX = 48
    MATCHBOOK = 49
    MOVIE_CAMERA = 52
    PAPER = 54
    PLAQUE = 55
    SHORT_SIGN = 56
    SIGN = 57
    PLANT = 58
    RING = 60
    ROCK = 61
    SECURITY_DEV = 63
    SENSOR = 64
    SIGN_OLD = 65  # kept for backwards compat with seed data
    SKATEBOARD = 67
    SKY = 69
    STREET = 70
    TAPE = 71
    TELEPORT = 74
    TICKET = 75
    TOKENS = 76
    WALL = 80
    WINDUP_TOY = 82
    CHANGOMATIC = 84
    VENDO_FRONT = 85
    VENDO_INSIDE = 86
    TRAPEZOID = 87
    HOLE = 88
    SHOVEL = 89
    SEX_CHANGER = 90
    STUN_GUN = 91
    SUPER_TRAPEZOID = 92
    FLAT = 93
    SPRAY_CAN = 95
    PAWN_MACHINE = 96
    SWITCH = 97
    GLUE = 98
    HEAD = 127
    AQUARIUM = 129
    BED = 130
    BRIDGE = 131
    BUILDING = 132
    BUSH = 133
    CHAIR = 134
    CHEST = 135
    COKE_MACHINE = 136
    COUCH = 137
    FENCE = 138
    FLOOR_LAMP = 139
    FORTUNE_MACHINE = 140
    FOUNTAIN = 141
    HOUSE_CAT = 143
    HOT_TUB = 144
    JUKEBOX = 145
    POND = 147
    RIVER = 148
    ROOF = 149
    SAFE = 150
    PICTURE = 152
    STEREO = 153
    STREETLAMP = 154
    TABLE = 155
    TREE = 156
    WINDOW = 157
    BUREAUCRAT = 158
    SHIRT = 159
    PANTS = 160
    GEMSTONE = 161


class Posture(IntEnum):
    STAND = 129
    SIT_GROUND = 132
    SIT_CHAIR = 133
    STAND_FRONT = 146
    SIT_FRONT = 157
    STAND_LEFT = 251
    STAND_RIGHT = 252
    COLOR_POSTURE = 253
    FACE_LEFT = 254
    FACE_RIGHT = 255


class CurseType(IntEnum):
    NONE = 0
    COOTIES = 1
    SMILEY = 2
    MUTANT = 3
    FLY = 4


# --- Data models (from PL/I BASED structures) ---

@dataclass
class GameObject:
    """Base object. From struct_gen_object.incl.pl1"""
    noid: int = 0
    class_id: int = 0
    x: int = 0
    y: int = 0
    orientation: int = 0
    gr_state: int = 0
    container_noid: int = 0
    position: int = 0
    style: int = 0
    # Extra fields for specific classes
    extra: dict = field(default_factory=dict)


@dataclass
class Avatar:
    """Player avatar. From struct_avatar.incl.pl1"""
    noid: int = 0
    x: int = 80
    y: int = 130
    orientation: int = 0
    gr_state: int = 0
    container_noid: int = 0
    position: int = 0
    style: int = 0
    activity: int = Posture.STAND_FRONT
    action: int = 0
    health: int = 255
    stun_count: int = 0
    bank_account: int = 5000
    tokens_in_hand: int = 100
    curse_type: int = CurseType.NONE
    name: str = ""
    turf_region: int = 0
    # Statistics
    deaths: int = 0
    kills: int = 0
    travel: int = 0
    teleports: int = 0
    talk_count: int = 0


@dataclass
class Region:
    """A room/area. From region.structs.incl.pl1"""
    region_id: int = 0
    name: str = ""
    terrain_type: int = 0
    x_size: int = 160
    y_size: int = 255
    orientation: int = 0
    depth: int = 0
    # Neighbors (region_id or 0 for none)
    neighbor_west: int = 0
    neighbor_east: int = 0
    neighbor_north: int = 0
    neighbor_south: int = 0
    # Lighting
    lighting: int = 1


@dataclass
class DoorObject(GameObject):
    """Door connecting regions. From class_door.pl1"""
    connection: int = 0  # destination region_id
    open_flags: int = 0
    locked: bool = False
    key_noid: int = 0


@dataclass
class TeleportObject(GameObject):
    """Teleport booth. From class_teleport.pl1"""
    COST: int = 10
    state: int = 0  # 0=ready, 1=active
    destination: int = 0
    take: int = 0  # revenue collected


@dataclass
class ATMObject(GameObject):
    """Bank ATM. From class_atm.pl1"""
    pass


@dataclass
class VendoObject(GameObject):
    """Vending machine. From class_vendo_front.pl1"""
    display_item: int = 0
    item_price: int = 0
    take: int = 0
    prices: list = field(default_factory=lambda: [10, 20, 30, 50, 100])
    items: list = field(default_factory=list)


@dataclass
class MailboxObject(GameObject):
    """Mailbox. From class_mailbox.pl1"""
    messages: list = field(default_factory=list)


@dataclass
class GunObject(GameObject):
    """Weapon. From class_gun.pl1"""
    damage: int = 10
    ammo: int = 6


@dataclass
class ContainerObject(GameObject):
    """Bag/box. From generic container."""
    capacity: int = 5
    contents: list = field(default_factory=list)


@dataclass
class SignObject(GameObject):
    """Sign/plaque. From class_sign.pl1"""
    text: str = ""


@dataclass
class PaperObject(GameObject):
    """Writable paper. From class_paper.pl1"""
    text: str = ""
    author: str = ""


@dataclass
class KeyObject(GameObject):
    """Key for locks. From class_key.pl1"""
    key_id: int = 0


@dataclass
class TokensObject(GameObject):
    """Currency tokens. From class_tokens.pl1"""
    denomination: int = 0
