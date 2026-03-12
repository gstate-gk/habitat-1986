from .base import BaseObject, OBJECT_REGISTRY
from .avatar import AvatarHandler
from .door import DoorHandler
from .teleport import TeleportHandler
from .atm import ATMHandler
from .vendo import VendoHandler
from .mailbox import MailboxHandler
from .gun import GunHandler
from .sign import SignHandler
from .paper import PaperHandler
from .key import KeyHandler
from .bag import BagHandler
from .tokens import TokensHandler
from .ground import GroundHandler
from .region_obj import RegionHandler
from .static import StaticHandler
from .portable import PortableHandler
from .containers import ContainerHandler
from .weapons import WeaponHandler
from .wearable import WearableHandler
from .magic import MagicHandler
from .machines import MachineHandler
from .creatures import CreatureHandler
from .special import ReadableHandler, HandOfGodHandler, SexChangerHandler


def register_all():
    """Initialize all object handlers into OBJECT_REGISTRY.
    Replaces PL/I: initialize_class_avatar, initialize_class_door, etc.
    All 107+ original PL/I classes are now registered."""
    from ..models import ClassID

    # --- Core (already existed) ---
    OBJECT_REGISTRY[ClassID.AVATAR] = AvatarHandler()
    OBJECT_REGISTRY[ClassID.DOOR] = DoorHandler()
    OBJECT_REGISTRY[ClassID.TELEPORT] = TeleportHandler()
    OBJECT_REGISTRY[ClassID.ATM] = ATMHandler()
    OBJECT_REGISTRY[ClassID.VENDO_FRONT] = VendoHandler()
    OBJECT_REGISTRY[ClassID.VENDO_INSIDE] = VendoHandler()
    OBJECT_REGISTRY[ClassID.MAILBOX] = MailboxHandler()
    OBJECT_REGISTRY[ClassID.GUN] = GunHandler()
    OBJECT_REGISTRY[ClassID.SIGN] = SignHandler()
    OBJECT_REGISTRY[ClassID.SIGN_OLD] = SignHandler()
    OBJECT_REGISTRY[ClassID.PAPER] = PaperHandler()
    OBJECT_REGISTRY[ClassID.KEY] = KeyHandler()
    OBJECT_REGISTRY[ClassID.BAG] = BagHandler()
    OBJECT_REGISTRY[ClassID.TOKENS] = TokensHandler()
    OBJECT_REGISTRY[ClassID.GROUND] = GroundHandler()
    OBJECT_REGISTRY[ClassID.STREET] = GroundHandler()
    OBJECT_REGISTRY[ClassID.REGION] = RegionHandler()

    # --- Static / Scenery / Furniture ---
    _static = StaticHandler()
    for cid in (
        ClassID.TREE, ClassID.BUSH, ClassID.PLANT, ClassID.ROCK,
        ClassID.RIVER, ClassID.POND, ClassID.FOUNTAIN, ClassID.SKY,
        ClassID.ROOF, ClassID.BRIDGE, ClassID.FENCE, ClassID.WALL,
        ClassID.WINDOW, ClassID.BUILDING, ClassID.STREETLAMP,
        ClassID.FLAT, ClassID.TRAPEZOID, ClassID.SUPER_TRAPEZOID,
        ClassID.BED, ClassID.CHAIR, ClassID.COUCH, ClassID.TABLE,
        ClassID.COUNTERTOP, ClassID.FLOOR_LAMP, ClassID.AQUARIUM,
        ClassID.HOT_TUB, ClassID.JUKEBOX, ClassID.ELEVATOR,
        ClassID.HOLE, ClassID.PICTURE, ClassID.FLAG, ClassID.KNICK_KNACK,
        ClassID.STEREO,
    ):
        OBJECT_REGISTRY[cid] = _static

    # --- Portable items ---
    _portable = PortableHandler()
    for cid in (
        ClassID.FLASHLIGHT, ClassID.SHOVEL, ClassID.COMPASS,
        ClassID.TAPE, ClassID.GLUE, ClassID.SPRAY_CAN,
        ClassID.MATCHBOOK, ClassID.BOTTLE, ClassID.DRUGS,
        ClassID.SKATEBOARD, ClassID.FRISBEE, ClassID.BALL,
        ClassID.WINDUP_TOY, ClassID.MOVIE_CAMERA, ClassID.TICKET,
        ClassID.GAME_PIECE, ClassID.DIE, ClassID.INSTANT_OBJECT,
        ClassID.ESCAPE_DEV, ClassID.SENSOR, ClassID.SECURITY_DEV,
        ClassID.HEAD, ClassID.GEMSTONE,
    ):
        OBJECT_REGISTRY[cid] = _portable

    # --- Containers ---
    _container = ContainerHandler()
    for cid in (
        ClassID.BOX, ClassID.CHEST, ClassID.SAFE,
        ClassID.DISPLAY_CASE, ClassID.GARBAGE_CAN, ClassID.DROPBOX,
    ):
        OBJECT_REGISTRY[cid] = _container

    # --- Weapons ---
    _weapon = WeaponHandler()
    for cid in (
        ClassID.KNIFE, ClassID.CLUB, ClassID.BOOMERANG,
        ClassID.STUN_GUN, ClassID.FAKE_GUN, ClassID.GRENADE,
    ):
        OBJECT_REGISTRY[cid] = _weapon

    # --- Wearable ---
    _wearable = WearableHandler()
    for cid in (
        ClassID.HAT, ClassID.JACKET, ClassID.SHIRT, ClassID.PANTS,
    ):
        OBJECT_REGISTRY[cid] = _wearable

    # --- Magic ---
    _magic = MagicHandler()
    for cid in (
        ClassID.AMULET, ClassID.RING, ClassID.CRYSTAL_BALL,
        ClassID.MAGIC_LAMP, ClassID.MAGIC_STAFF, ClassID.MAGIC_WAND,
    ):
        OBJECT_REGISTRY[cid] = _magic

    # --- Machines ---
    _machine = MachineHandler()
    for cid in (
        ClassID.COKE_MACHINE, ClassID.FORTUNE_MACHINE,
        ClassID.PAWN_MACHINE, ClassID.CHANGOMATIC, ClassID.SWITCH,
    ):
        OBJECT_REGISTRY[cid] = _machine

    # --- Creatures ---
    _creature = CreatureHandler()
    for cid in (
        ClassID.GHOST, ClassID.HOUSE_CAT, ClassID.BUREAUCRAT,
    ):
        OBJECT_REGISTRY[cid] = _creature

    # --- Readable (plaque, short_sign, book) ---
    _readable = ReadableHandler()
    for cid in (
        ClassID.PLAQUE, ClassID.SHORT_SIGN, ClassID.BOOK,
    ):
        OBJECT_REGISTRY[cid] = _readable

    # --- Special ---
    OBJECT_REGISTRY[ClassID.HAND_OF_GOD] = HandOfGodHandler()
    OBJECT_REGISTRY[ClassID.SEX_CHANGER] = SexChangerHandler()
