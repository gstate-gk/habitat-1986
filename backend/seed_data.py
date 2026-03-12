"""
Seed the database with initial world data.
Creates a rich Habitat world with all object types represented.
"""
import asyncio
import json
import aiosqlite
from .database import DB_PATH, init_db
from .models import ClassID


REGIONS = [
    (1, "Town Square", 0, 320, 255, 1, 0, 3, 4, 0, 0),
    (2, "First Bank of Habitat", 0, 200, 200, 1, 0, 0, 0, 0, 0),
    (3, "General Store", 0, 200, 200, 1, 1, 0, 0, 0, 0),
    (4, "Habitat Park", 1, 400, 255, 1, 0, 0, 5, 1, 0),
    (5, "Teleport Hub", 0, 200, 200, 1, 0, 0, 0, 4, 0),
    (6, "Haunted House", 0, 250, 200, 0, 0, 0, 0, 0, 0),
    (7, "Chip's Lounge", 0, 250, 200, 1, 0, 0, 0, 0, 0),
]

OBJECTS = [
    # === Town Square ===
    (ClassID.SIGN_OLD, 1, 160, 200, 0, 0, 0, 0, 0,
     json.dumps({"text": "Welcome to Habitat! The world's first MMO, circa 1986."})),
    (ClassID.GROUND, 1, 0, 0, 0, 0, 0, 0, 0, "{}"),
    (ClassID.DOOR, 1, 40, 140, 0, 0, 0, 0, 0,
     json.dumps({"connection": 2, "text": "Bank"})),
    (ClassID.DOOR, 1, 280, 140, 0, 0, 0, 0, 0,
     json.dumps({"connection": 3, "text": "Store"})),
    (ClassID.DOOR, 1, 160, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 4, "text": "Park"})),
    (ClassID.MAILBOX, 1, 240, 200, 0, 0, 0, 0, 0,
     json.dumps({"messages": [
         {"from": "Chip Morningstar", "to": "all",
          "text": "Welcome to Habitat! Remember: be excellent to each other."}
     ]})),
    (ClassID.TREE, 1, 60, 200, 0, 0, 0, 0, 0, "{}"),
    (ClassID.FOUNTAIN, 1, 160, 120, 0, 0, 0, 0, 0, "{}"),
    (ClassID.STREETLAMP, 1, 300, 200, 0, 0, 0, 0, 0, "{}"),
    (ClassID.DOOR, 1, 100, 200, 0, 0, 0, 0, 0,
     json.dumps({"connection": 6, "text": "Haunted House"})),
    (ClassID.DOOR, 1, 220, 100, 0, 0, 0, 0, 0,
     json.dumps({"connection": 7, "text": "Chip's Lounge"})),

    # === Bank ===
    (ClassID.ATM, 2, 100, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.SIGN_OLD, 2, 100, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "First Bank of Habitat — Deposits & Withdrawals"})),
    (ClassID.DOOR, 2, 100, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 1, "text": "Exit to Town Square"})),
    (ClassID.TOKENS, 2, 60, 60, 0, 0, 0, 0, 0,
     json.dumps({"denomination": 50})),
    (ClassID.SAFE, 2, 160, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.SECURITY_DEV, 2, 30, 180, 0, 0, 0, 0, 0, "{}"),
    (ClassID.PLAQUE, 2, 160, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "FDIC insured. Your tokens are safe with us."})),

    # === Store ===
    (ClassID.VENDO_FRONT, 3, 100, 120, 0, 0, 0, 0, 0,
     json.dumps({
         "items": ["Flashlight", "Key", "Paper", "Bag", "Gun"],
         "prices": [10, 25, 5, 30, 100],
         "display_item": 0,
     })),
    (ClassID.SIGN_OLD, 3, 100, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "Habitat General Store — Browse & Buy!"})),
    (ClassID.DOOR, 3, 100, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 1, "text": "Exit to Town Square"})),
    (ClassID.DISPLAY_CASE, 3, 50, 120, 0, 0, 0, 0, 0, "{}"),
    (ClassID.COUNTERTOP, 3, 150, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.KNIFE, 3, 60, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.FLASHLIGHT, 3, 140, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.BOTTLE, 3, 70, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.SHOVEL, 3, 170, 60, 0, 0, 0, 0, 0, "{}"),

    # === Park ===
    (ClassID.SIGN_OLD, 4, 200, 200, 0, 0, 0, 0, 0,
     json.dumps({"text": "Habitat Park — A peaceful place to rest."})),
    (ClassID.GROUND, 4, 0, 0, 0, 0, 0, 0, 0,
     json.dumps({"terrain": "grass"})),
    (ClassID.DOOR, 4, 200, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 5, "text": "Teleport Hub"})),
    (ClassID.DOOR, 4, 200, 240, 0, 0, 0, 0, 0,
     json.dumps({"connection": 1, "text": "Town Square"})),
    (ClassID.PAPER, 4, 120, 100, 0, 0, 0, 0, 0,
     json.dumps({"text": "I was here! — Phread, 1986", "author": "Phread"})),
    (ClassID.GUN, 4, 300, 80, 0, 0, 0, 0, 0,
     json.dumps({"damage": 10, "ammo": 6, "class_name": "gun"})),
    (ClassID.TREE, 4, 80, 180, 0, 0, 0, 0, 0, "{}"),
    (ClassID.TREE, 4, 320, 180, 0, 0, 0, 0, 0, "{}"),
    (ClassID.BUSH, 4, 150, 160, 0, 0, 0, 0, 0, "{}"),
    (ClassID.POND, 4, 250, 120, 0, 0, 0, 0, 0, "{}"),
    (ClassID.ROCK, 4, 350, 150, 0, 0, 0, 0, 0, "{}"),
    (ClassID.PLANT, 4, 50, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.HOUSE_CAT, 4, 180, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.BALL, 4, 100, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.FRISBEE, 4, 280, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.SHORT_SIGN, 4, 220, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "In memory of the Commodore 64."})),

    # === Teleport Hub ===
    (ClassID.TELEPORT, 5, 60, 100, 0, 0, 0, 0, 0,
     json.dumps({"destination": 1})),
    (ClassID.TELEPORT, 5, 140, 100, 0, 0, 0, 0, 0,
     json.dumps({"destination": 4})),
    (ClassID.SIGN_OLD, 5, 100, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "Teleport Hub — 10 tokens per trip"})),
    (ClassID.DOOR, 5, 100, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 4, "text": "Exit to Park"})),
    (ClassID.COKE_MACHINE, 5, 160, 140, 0, 0, 0, 0, 0, "{}"),
    (ClassID.FORTUNE_MACHINE, 5, 40, 140, 0, 0, 0, 0, 0, "{}"),

    # === Haunted House ===
    (ClassID.GHOST, 6, 125, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.SIGN_OLD, 6, 125, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "The Haunted House of Habitat"})),
    (ClassID.DOOR, 6, 125, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 1, "text": "Exit to Town Square"})),
    (ClassID.MAGIC_LAMP, 6, 60, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.CRYSTAL_BALL, 6, 190, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.AMULET, 6, 125, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.CHEST, 6, 80, 140, 0, 0, 0, 0, 0, "{}"),
    (ClassID.BOOK, 6, 170, 140, 0, 0, 0, 0, 0,
     json.dumps({"text": "The Lessons of Lucasfilm's Habitat — Morningstar & Farmer", "author": "Chip Morningstar"})),
    (ClassID.HOLE, 6, 200, 40, 0, 0, 0, 0, 0, "{}"),

    # === Chip's Lounge ===
    (ClassID.SIGN_OLD, 7, 125, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "Chip's Lounge — Relax and chat!"})),
    (ClassID.DOOR, 7, 125, 20, 0, 0, 0, 0, 0,
     json.dumps({"connection": 1, "text": "Exit to Town Square"})),
    (ClassID.COUCH, 7, 60, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.TABLE, 7, 125, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.CHAIR, 7, 100, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.CHAIR, 7, 150, 80, 0, 0, 0, 0, 0, "{}"),
    (ClassID.JUKEBOX, 7, 200, 160, 0, 0, 0, 0, 0, "{}"),
    (ClassID.FLOOR_LAMP, 7, 30, 160, 0, 0, 0, 0, 0, "{}"),
    (ClassID.PICTURE, 7, 125, 180, 0, 0, 0, 0, 0,
     json.dumps({"text": "Portrait of George Lucas"})),
    (ClassID.COKE_MACHINE, 7, 220, 100, 0, 0, 0, 0, 0, "{}"),
    (ClassID.CHANGOMATIC, 7, 40, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.BUREAUCRAT, 7, 180, 60, 0, 0, 0, 0, 0, "{}"),
    (ClassID.HAT, 7, 90, 140, 0, 0, 0, 0, 0, "{}"),
    (ClassID.RING, 7, 160, 140, 0, 0, 0, 0, 0, "{}"),
    (ClassID.DIE, 7, 130, 120, 0, 0, 0, 0, 0, "{}"),
]

async def seed():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if already seeded
        async with db.execute("SELECT COUNT(*) FROM regions") as cur:
            count = (await cur.fetchone())[0]
            if count > 0:
                print("Database already seeded.")
                return

        for r in REGIONS:
            await db.execute("""
                INSERT INTO regions (region_id, name, terrain_type, x_size, y_size,
                    lighting, neighbor_west, neighbor_east, neighbor_north,
                    neighbor_south, depth)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, r)

        for o in OBJECTS:
            await db.execute("""
                INSERT INTO objects (class_id, region_id, x, y, orientation,
                    gr_state, container_noid, position, style, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, o)

        await db.commit()
        print(f"Seeded {len(REGIONS)} regions and {len(OBJECTS)} objects.")


if __name__ == "__main__":
    asyncio.run(seed())
