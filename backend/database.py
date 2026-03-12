"""
Database layer.
Converted from: habitat_db.pl1 (1,426 lines)

Original PL/I used Stratus VOS keyed/indexed files:
    s$open(region_port, seq_org, region_size, ...);
    s$keyed_read(region_port, 'ident', '', region_size, ...);

Python equivalent: aiosqlite with async operations.
"""
from __future__ import annotations
import json
import aiosqlite
from pathlib import Path

from .models import Region, GameObject, Avatar, ClassID

DB_PATH = Path(__file__).parent / "habitat.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS regions (
                region_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                terrain_type INTEGER DEFAULT 0,
                x_size INTEGER DEFAULT 160,
                y_size INTEGER DEFAULT 255,
                orientation INTEGER DEFAULT 0,
                depth INTEGER DEFAULT 0,
                lighting INTEGER DEFAULT 1,
                neighbor_west INTEGER DEFAULT 0,
                neighbor_east INTEGER DEFAULT 0,
                neighbor_north INTEGER DEFAULT 0,
                neighbor_south INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS objects (
                noid INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                region_id INTEGER NOT NULL,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                orientation INTEGER DEFAULT 0,
                gr_state INTEGER DEFAULT 0,
                container_noid INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                style INTEGER DEFAULT 0,
                extra TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS avatars (
                noid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                x INTEGER DEFAULT 80,
                y INTEGER DEFAULT 130,
                orientation INTEGER DEFAULT 0,
                activity INTEGER DEFAULT 146,
                health INTEGER DEFAULT 255,
                bank_account INTEGER DEFAULT 5000,
                tokens_in_hand INTEGER DEFAULT 100,
                curse_type INTEGER DEFAULT 0,
                turf_region INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                travel INTEGER DEFAULT 0,
                teleports INTEGER DEFAULT 0,
                talk_count INTEGER DEFAULT 0,
                current_region INTEGER DEFAULT 1
            );
        """)
        await db.commit()


async def get_region(region_id: int) -> Region | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM regions WHERE region_id = ?", (region_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return Region(**dict(row))


async def get_region_objects(region_id: int) -> list[GameObject]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM objects WHERE region_id = ?", (region_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                extra = json.loads(d.pop("extra", "{}"))
                d.pop("region_id", None)
                result.append(GameObject(**d, extra=extra))
            return result


async def save_avatar(avatar: Avatar, region_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO avatars (name, x, y, orientation, activity, health,
                bank_account, tokens_in_hand, curse_type, turf_region,
                deaths, kills, travel, teleports, talk_count, current_region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x=excluded.x, y=excluded.y, health=excluded.health,
                bank_account=excluded.bank_account,
                tokens_in_hand=excluded.tokens_in_hand,
                deaths=excluded.deaths, kills=excluded.kills,
                travel=excluded.travel, teleports=excluded.teleports,
                talk_count=excluded.talk_count, current_region=excluded.current_region
        """, (avatar.name, avatar.x, avatar.y, avatar.orientation,
              avatar.activity, avatar.health, avatar.bank_account,
              avatar.tokens_in_hand, avatar.curse_type, avatar.turf_region,
              avatar.deaths, avatar.kills, avatar.travel, avatar.teleports,
              avatar.talk_count, region_id))
        await db.commit()


async def load_avatar(name: str) -> tuple[Avatar, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM avatars WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            region_id = d.pop("current_region", 1)
            return Avatar(**d), region_id
