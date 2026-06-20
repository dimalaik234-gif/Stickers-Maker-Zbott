# database.py
import aiosqlite
from config import DATABASE_PATH


async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                pack_short_name TEXT,
                lang TEXT DEFAULT 'ru'
            )
        """)
        await db.commit()


async def get_user_pack(user_id: int) -> str | None:
    """Fetch the user's sticker pack short name."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT pack_short_name FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_user_pack(user_id: int, pack_short_name: str):
    """Set or update the user's sticker pack short name."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, pack_short_name, lang)
            VALUES (?, ?, 'ru')
            ON CONFLICT(user_id) DO UPDATE SET pack_short_name = ?
        """, (user_id, pack_short_name, pack_short_name))
        await db.commit()


async def get_user_lang(user_id: int) -> str:
    """Fetch the user's language preference."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT lang FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'ru'


async def set_user_lang(user_id: int, lang: str):
    """Set or update the user's language preference."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, lang)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang = ?
        """, (user_id, lang, lang))
        await db.commit()
