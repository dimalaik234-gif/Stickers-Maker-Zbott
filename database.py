# database.py
import aiosqlite
from config import DATABASE_PATH


async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'ru',
                current_pack_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица стикерпаков
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sticker_packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pack_name TEXT NOT NULL,
                pack_title TEXT NOT NULL,
                pack_type TEXT DEFAULT 'regular',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, pack_name)
            )
        """)
        
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


async def create_sticker_pack(user_id: int, pack_name: str, pack_title: str, pack_type: str = 'regular'):
    """Create a new sticker pack record."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO sticker_packs (user_id, pack_name, pack_title, pack_type)
            VALUES (?, ?, ?, ?)
        """, (user_id, pack_name, pack_title, pack_type))
        
        pack_id = (await db.execute("SELECT last_insert_rowid()")).fetchone()[0]
        
        # Set as current pack
        await db.execute("""
            UPDATE users SET current_pack_id = ? WHERE user_id = ?
        """, (pack_id, user_id))
        
        await db.commit()
        return pack_id


async def get_user_packs(user_id: int):
    """Get all sticker packs for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT id, pack_name, pack_title, pack_type, created_at
            FROM sticker_packs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()


async def get_current_pack(user_id: int):
    """Get user's current active pack."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT sp.id, sp.pack_name, sp.pack_title, sp.pack_type
            FROM sticker_packs sp
            JOIN users u ON u.current_pack_id = sp.id
            WHERE u.user_id = ?
        """, (user_id,)) as cursor:
            return await cursor.fetchone()


async def set_current_pack(user_id: int, pack_id: int):
    """Set user's current active pack."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET current_pack_id = ? WHERE user_id = ?
        """, (pack_id, user_id))
        await db.commit()


async def get_pack_by_name(user_id: int, pack_name: str):
    """Get pack by name."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT id, pack_name, pack_title, pack_type
            FROM sticker_packs
            WHERE user_id = ? AND pack_name = ?
        """, (user_id, pack_name)) as cursor:
            return await cursor.fetchone()


async def delete_pack(pack_id: int):
    """Delete a sticker pack record."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM sticker_packs WHERE id = ?", (pack_id,))
        await db.commit()
