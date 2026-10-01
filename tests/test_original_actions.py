"""Tests for the original-PL/I-faithful actions, timers, curses and persistence."""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Avatar, ClassID, CurseType, GameObject, Region
from backend.region_processor import RegionProcessor
from backend.objects import register_all
from backend.objects.weapons import WeaponHandler
from backend.fortunes_data import FORTUNES
from backend.curses import buzzify, curse_touch
from backend import helpers

register_all()


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, m):
        self.sent.append(m)


def run(coro):
    return asyncio.run(coro)


class World:
    def __init__(self, names=("alice",)):
        self.region = RegionProcessor(Region(region_id=1, name="t"))
        self.t = [0.0]
        self.region.clock = lambda: self.t[0]
        self.ws = FakeWS()
        self.avatars = {}
        for n in names:
            a = Avatar(name=n)
            self.region.add_avatar(a, self.ws)
            self.avatars[n] = a

    def obj(self, cid, **kw):
        o = GameObject(class_id=int(cid), **kw)
        self.region.add_object(o)
        return o

    def do(self, who, obj, action="DO", **args):
        a = self.avatars[who]
        return run(self.region.handle_message(
            a.noid, {"action": action, "noid": obj.noid, "args": args}))


# --- priority 1: inventions removed ---

def test_coke_machine_pay_no_health_gain():
    w = World()
    a = w.avatars["alice"]
    a.health = 100
    coke = w.obj(ClassID.COKE_MACHINE)
    r = w.do("alice", coke)
    assert r["success"] and a.tokens_in_hand == 95 and a.health == 100


def test_coke_machine_insufficient_funds():
    w = World()
    a = w.avatars["alice"]
    a.tokens_in_hand = 4
    r = w.do("alice", w.obj(ClassID.COKE_MACHINE))
    assert not r["success"] and a.tokens_in_hand == 4


def test_fortunes_are_the_original_90():
    assert len(FORTUNES) == 90
    w = World()
    a = w.avatars["alice"]
    r = w.do("alice", w.obj(ClassID.FORTUNE_MACHINE))
    assert r["text"] in FORTUNES and a.tokens_in_hand == 98


def test_hand_of_god_does_not_heal():
    w = World()
    a = w.avatars["alice"]
    a.health = 10
    r = w.do("alice", w.obj(ClassID.HAND_OF_GOD))
    assert not r["success"] and a.health == 10 and a.tokens_in_hand == 100


def test_ghost_has_no_attack():
    w = World()
    g = w.obj(ClassID.GHOST)
    for _ in range(50):
        w.do("alice", g)
    assert w.avatars["alice"].health == 255


def test_weapon_damage_is_flat_20_and_gun_has_no_ammo():
    w = World(("alice", "bob"))
    a, b = w.avatars["alice"], w.avatars["bob"]
    gun = w.obj(ClassID.GUN, container_noid=a.noid)
    for cid in (ClassID.KNIFE, ClassID.CLUB):
        k = w.obj(cid, container_noid=a.noid)
        b.health = 255
        w.do("alice", k)
        assert b.health == 235
    b.health = 255
    r = w.do("alice", gun, target=b.noid)
    assert r["success"] and b.health == 235
    assert not hasattr(WeaponHandler, "DAMAGE_TABLE")


def test_attack_kills_with_original_penalties():
    w = World(("alice", "bob"))
    a, b = w.avatars["alice"], w.avatars["bob"]
    gun = w.obj(ClassID.GUN, container_noid=a.noid)
    held = w.obj(ClassID.KEY, container_noid=b.noid)
    b.health = 20
    b.bank_account = 1000
    w.do("alice", gun, "ATTACK", target=b.noid)
    assert b.health == 255 and b.deaths == 1 and b.bank_account == 800
    assert held.container_noid == 0 and a.kills == 1


def test_attack_blocked_when_stunned_or_weapons_free():
    w = World(("alice", "bob"))
    a, b = w.avatars["alice"], w.avatars["bob"]
    gun = w.obj(ClassID.GUN, container_noid=a.noid)
    a.stun_count = 1
    w.do("alice", gun, "ATTACK", target=b.noid)
    assert b.health == 255
    a.stun_count = 0
    w.region.region.weapons_free = True
    w.do("alice", gun, "ATTACK", target=b.noid)
    assert b.health == 255


# --- priority 2: class actions ---

def test_die_roll_range():
    w = World()
    d = w.obj(ClassID.DIE)
    seen = {w.do("alice", d)["gr_state"] for _ in range(100)}
    assert seen <= set(range(6)) and len(seen) > 1


def test_drugs_heal_poison_and_consumption():
    w = World()
    a = w.avatars["alice"]
    a.health = 50
    heal = w.obj(ClassID.DRUGS, container_noid=a.noid, extra={"effect": 1, "count": 2})
    assert w.do("alice", heal)["success"] and a.health == 255
    assert heal.extra["count"] == 1
    w.do("alice", heal)
    assert heal.noid not in w.region.objects
    poison = w.obj(ClassID.DRUGS, container_noid=a.noid, extra={"effect": 2, "count": 1})
    w.do("alice", poison)
    assert a.deaths == 1


def test_drugs_need_to_be_held():
    w = World()
    p = w.obj(ClassID.DRUGS, extra={"effect": 2, "count": 1})
    assert not w.do("alice", p)["success"]


def test_bottle_fill_pour_cycle():
    w = World()
    b = w.obj(ClassID.BOTTLE, container_noid=w.avatars["alice"].noid)
    assert w.do("alice", b)["success"] and b.extra["filled"]
    assert not w.do("alice", b, "FILL")["success"]
    assert w.do("alice", b)["success"] and not b.extra["filled"]


def test_sex_changer_toggles_bit_8():
    w = World()
    a = w.avatars["alice"]
    s = w.obj(ClassID.SEX_CHANGER)
    w.do("alice", s)
    assert helpers.test_bit(a.orientation, 8)
    w.do("alice", s)
    assert not helpers.test_bit(a.orientation, 8)


def test_compass_and_game_piece():
    w = World()
    c = w.obj(ClassID.COMPASS, gr_state=2)
    assert w.do("alice", c)["success"]
    g = w.obj(ClassID.GAME_PIECE, gr_state=6)
    w.do("alice", g)
    assert g.gr_state == 7


def test_stun_gun_stuns_target():
    w = World(("alice", "bob"))
    gun = w.obj(ClassID.STUN_GUN, container_noid=w.avatars["alice"].noid)
    w.do("alice", gun)
    assert w.avatars["bob"].stun_count > 0


def test_spray_can_paints_torso_and_runs_out():
    w = World()
    a = w.avatars["alice"]
    can = w.obj(ClassID.SPRAY_CAN, container_noid=a.noid, orientation=0x28,
                extra={"charge": 1})
    w.do("alice", can, limb=1)
    assert a.customize[0] & 0x0F == 0x28 // 8
    assert can.noid not in w.region.objects


# --- priority 3: timers ---

def test_grenade_explodes_after_20_seconds_only():
    w = World(("alice", "bob"))
    a, b = w.avatars["alice"], w.avatars["bob"]
    g = w.obj(ClassID.GRENADE, container_noid=a.noid)
    assert w.do("alice", g)["success"]
    w.t[0] = 19.9
    run(w.region.process_tact())
    assert g.noid in w.region.objects and b.health == 255
    w.t[0] = 20.1
    run(w.region.process_tact())
    assert g.noid not in w.region.objects
    assert b.health == 235 and a.health == 235


def test_grenade_pin_only_once_and_weapons_free():
    w = World()
    g = w.obj(ClassID.GRENADE, container_noid=w.avatars["alice"].noid)
    assert w.do("alice", g)["success"]
    assert not w.do("alice", g)["success"]
    w2 = World()
    w2.region.region.weapons_free = True
    g2 = w2.obj(ClassID.GRENADE, container_noid=w2.avatars["alice"].noid)
    assert not w2.do("alice", g2)["success"]


def test_clear_tact():
    w = World()
    fired = []

    async def cb(region):
        fired.append(1)
    h = w.region.tact(5, cb)
    assert w.region.clear_tact(h)
    w.t[0] = 10
    run(w.region.process_tact())
    assert not fired


def test_magic_lamp_wish_flow_and_timeouts():
    w = World()
    a = w.avatars["alice"]
    lamp = w.obj(ClassID.MAGIC_LAMP, container_noid=a.noid)
    assert w.do("alice", lamp)["success"]               # RUB
    r = w.do("alice", lamp, text="a pony")               # WISH
    assert r["success"] and lamp.noid not in w.region.objects
    lamp2 = w.obj(ClassID.MAGIC_LAMP, container_noid=a.noid)
    w.do("alice", lamp2)
    w.t[0] = 31
    run(w.region.process_tact())
    assert lamp2.noid in w.region.objects               # impatient, still there
    w.t[0] = 62
    run(w.region.process_tact())
    assert lamp2.noid not in w.region.objects


def test_boomerang_returns():
    w = World()
    a = w.avatars["alice"]
    b = w.obj(ClassID.BOOMERANG, container_noid=a.noid)
    w.do("alice", b)
    assert b.container_noid == -1
    w.t[0] = 31
    run(w.region.process_tact())
    assert b.container_noid == a.noid


# --- curses ---

def test_buzzify_matches_original_rule():
    assert buzzify("Hello world 42") == "Bzzzz bzzzz bz"
    assert buzzify("a") == "b"


def test_curse_spreads_and_expires():
    a, b = Avatar(name="a"), Avatar(name="b")
    a.curse_type = CurseType.COOTIES
    a.curse_counter = 1
    curse_touch(a, b)
    assert b.curse_type == CurseType.COOTIES and b.curse_counter == 1
    assert a.curse_type == CurseType.NONE and a.curse_immune


def test_smiley_has_two_infections():
    a, b, c = Avatar(name="a"), Avatar(name="b"), Avatar(name="c")
    a.curse_type, a.curse_counter = CurseType.SMILEY, 2
    curse_touch(a, b)
    curse_touch(a, c)
    assert b.curse_type == c.curse_type == CurseType.SMILEY
    assert a.curse_type == CurseType.NONE


def test_touch_action_infects():
    w = World(("alice", "bob"))
    a, b = w.avatars["alice"], w.avatars["bob"]
    a.curse_type, a.curse_counter = CurseType.MUTANT, 32767
    r = run(w.region.handle_message(a.noid, {"action": "TOUCH", "noid": a.noid,
                                              "args": {"target": b.noid}}))
    assert r["success"] and b.curse_type == CurseType.MUTANT


# --- persistence ---

@pytest.fixture
def tmpdb(tmp_path, monkeypatch):
    from backend import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "t.db")
    return database


def test_object_and_avatar_persistence(tmpdb):
    async def go():
        await tmpdb.init_db()
        import aiosqlite
        async with aiosqlite.connect(tmpdb.DB_PATH) as db:
            await db.execute("INSERT INTO regions (region_id, name) VALUES (1, 'x')")
            await db.commit()
        objs = [GameObject(noid=12, class_id=int(ClassID.BAG), x=5, y=6, extra={"k": 1}),
                GameObject(noid=13, class_id=int(ClassID.KEY), container_noid=12),
                GameObject(noid=14, class_id=int(ClassID.KNIFE), container_noid=77)]
        await tmpdb.save_region_objects(1, objs, {77: "alice"})
        back = {o.noid: o for o in await tmpdb.get_region_objects(1)}
        assert back[12].extra == {"k": 1} and back[13].container_noid == 12
        assert back[14].extra["_held_by"] == "alice" and back[14].container_noid == 0

        a = Avatar(name="alice", curse_type=CurseType.SMILEY, curse_counter=2,
                   curse_immune=True, true_head_style=4, customize=[3, 9])
        await tmpdb.save_avatar(a, 1)
        a.curse_type = CurseType.FLY
        await tmpdb.save_avatar(a, 1)
        loaded, rid = await tmpdb.load_avatar("alice")
        assert loaded.curse_type == CurseType.FLY and loaded.curse_counter == 2
        assert loaded.curse_immune and loaded.customize == [3, 9] and rid == 1
        reg = Region(region_id=1, weapons_free=True)
        await tmpdb.save_region_flags(reg)
        assert (await tmpdb.get_region(1)).weapons_free is True
    run(go())


def test_held_objects_survive_leave_and_return():
    w = World()
    a = w.avatars["alice"]
    key = w.obj(ClassID.KEY, container_noid=a.noid)
    w.region.detach_held(a.noid, "alice")
    assert key.noid not in w.region.objects and "alice" in w.region.stash
    from backend.main import adopt_held_objects
    adopt_held_objects(w.region, 55, "alice")
    assert w.region.objects[key.noid].container_noid == 55


# --- world data converter ---

def test_rdl_converter_parses_region_objects_and_nesting():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    import rdl_to_regions as rdl
    from collections import Counter
    text = """
    @region $ a_1 { north: b_1.l; region_orientation: FACE_EAST;
      [ @sign { x:8; y:66; or:8; style:6; gr_state:3; 8:84; 9:104; }
        @chest { x:1; y:2; @key { x:0; y:0; } }
        @teleport_booth { x:120; y:144; teleport_address: 80, 101; } ] }
    @region $ b_1 { south: a_1.l; [ ] }
    """
    regs = rdl.parse(text)
    assert [r["name"] for r in regs] == ["a_1", "b_1"]
    unknown = Counter()
    objs = [rdl.convert_object(c, unknown) for c in regs[0]["children"]]
    assert not unknown
    assert objs[0]["class_id"] == int(ClassID.SIGN) and objs[0]["slots"] == {"8": 84, "9": 104}
    assert objs[1]["children"][0]["class_id"] == int(ClassID.KEY)
    assert objs[2]["class_id"] == int(ClassID.TELEPORT)
