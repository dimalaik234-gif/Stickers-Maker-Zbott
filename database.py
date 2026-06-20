"""База данных пользователей и стикеров (aiosqlite)."""
import aiosqlite
from typing import Optional, List, Tuple
from config import DATABASE_PATH


class Database:
    """Асинхронная обёртка над SQLite для хранения пользователей и стикеров."""

    def __init__(self, path: str = DATABASE_PATH):
        self.path = path

    async def init(self) -> None:
        """Инициализировать таблицы."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    outline_color TEXT DEFAULT '#000000',
                    outline_width INTEGER DEFAULT 5,
                    watermark_text TEXT DEFAULT '',
                    default_font TEXT DEFAULT 'bold',
                    sticker_count INTEGER DEFAULT 0,
                    total_edits INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stickers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    emoji TEXT DEFAULT '😀',
                    pack_name TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER,
                    sticker_id INTEGER,
                    PRIMARY KEY (user_id, sticker_id)
                )
            """)
            # Индексы для ускорения выборок
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_stickers_user ON stickers(user_id, created_at DESC)"
            )
            await db.commit()

    # ---------- Пользователи ----------

    async def upsert_user(self, user_id: int, username: str, first_name: str) -> None:
        """Создать пользователя, если его нет."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
                """,
                (user_id, username, first_name),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Tuple]:
        """Получить данные пользователя."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                return await cursor.fetchone()

    async def update_setting(self, user_id: int, key: str, value) -> None:
        """Обновить пользовательскую настройку."""
        # Защита от SQL-инъекций: явно перечислим допустимые ключи
        allowed = {"outline_color", "outline_width", "watermark_text", "default_font"}
        if key not in allowed:
            raise ValueError(f"Недопустимый ключ настройки: {key}")

        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"UPDATE users SET {key} = ? WHERE user_id = ?",
                (value, user_id),
            )
            await db.commit()

    async def increment_stat(self, user_id: int, field: str) -> None:
        """Увеличить счётчик (sticker_count или total_edits)."""
        if field not in {"sticker_count", "total_edits"}:
            raise ValueError(f"Недопустимое поле: {field}")
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"UPDATE users SET {field} = {field} + 1 WHERE user_id = ?",
                (user_id,),
            )
            await db.commit()

    async def get_stats(self, user_id: int) -> dict:
        """Получить статистику пользователя."""
        user = await self.get_user(user_id)
        if not user:
            return {"sticker_count": 0, "total_edits": 0, "created_at": None}
        return {
            "sticker_count": user[8] or 0,
            "total_edits": user[9] or 0,
            "created_at": user[3],
        }

    # ---------- Стикеры ----------

    async def add_sticker(
        self, user_id: int, file_path: str, emoji: str = "😀", pack_name: str = None
    ) -> int:
        """Сохранить стикер и вернуть его ID."""
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO stickers (user_id, file_path, emoji, pack_name)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, file_path, emoji, pack_name),
            )
            sticker_id = cursor.lastrowid
            await db.execute(
                "UPDATE users SET sticker_count = sticker_count + 1 WHERE user_id = ?",
                (user_id,),
            )
            await db.commit()
            return sticker_id

    async def get_stickers(
        self, user_id: int, limit: int = 12, offset: int = 0
    ) -> List[Tuple]:
        """Получить список стикеров пользователя (с пагинацией)."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                """
                SELECT id, file_path, emoji, pack_name, created_at
                FROM stickers
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            ) as cursor:
                return await cursor.fetchall()

    async def count_stickers(self, user_id: int) -> int:
        """Подсчитать количество стикеров."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM stickers WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_sticker(self, sticker_id: int, user_id: int) -> Optional[Tuple]:
        """Получить один стикер (с проверкой владельца)."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT * FROM stickers WHERE id = ? AND user_id = ?",
                (sticker_id, user_id),
            ) as cursor:
                return await cursor.fetchone()

    async def delete_sticker(self, sticker_id: int, user_id: int) -> Optional[str]:
        """Удалить стикер, вернуть путь к файлу (для удаления с диска)."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT file_path FROM stickers WHERE id = ? AND user_id = ?",
                (sticker_id, user_id),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                file_path = row[0]
            await db.execute(
                "DELETE FROM stickers WHERE id = ? AND user_id = ?",
                (sticker_id, user_id),
            )
            await db.execute(
                """UPDATE users
                   SET sticker_count = MAX(0, sticker_count - 1)
                   WHERE user_id = ?""",
                (user_id,),
            )
            await db.commit()
            return file_path

    async def update_sticker_emoji(self, sticker_id: int, user_id: int, emoji: str) -> bool:
        """Сменить эмодзи стикера."""
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "UPDATE stickers SET emoji = ? WHERE id = ? AND user_id = ?",
                (emoji, sticker_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def update_sticker_pack(self, sticker_id: int, user_id: int, pack_name: str) -> bool:
        """Привязать стикер к паку."""
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "UPDATE stickers SET pack_name = ? WHERE id = ? AND user_id = ?",
                (pack_name, sticker_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    # ---------- Избранное ----------

    async def toggle_favorite(self, user_id: int, sticker_id: int) -> bool:
        """Добавить/убрать из избранного. Возвращает новое состояние."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT 1 FROM favorites WHERE user_id = ? AND sticker_id = ?",
                (user_id, sticker_id),
            ) as cursor:
                exists = await cursor.fetchone() is not None
            if exists:
                await db.execute(
                    "DELETE FROM favorites WHERE user_id = ? AND sticker_id = ?",
                    (user_id, sticker_id),
                )
                new_state = False
            else:
                await db.execute(
                    "INSERT INTO favorites (user_id, sticker_id) VALUES (?, ?)",
                    (user_id, sticker_id),
                )
                new_state = True
            await db.commit()
            return new_state
