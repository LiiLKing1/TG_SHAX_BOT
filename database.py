import aiosqlite
from typing import List, Dict, Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    genres TEXT NOT NULL,
                    channel_message_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    search_count INTEGER DEFAULT 0
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    media_number INTEGER NOT NULL,
                    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mandatory_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT UNIQUE NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
    
    async def add_media(self, number: int, title: str, media_type: str, genres: str, channel_message_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO media (number, title, type, genres, channel_message_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (number, title, media_type, genres, channel_message_id))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False
    
    async def get_media_by_number(self, number: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT number, title, type, genres, channel_message_id
                FROM media WHERE number = ?
            ''', (number,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'number': row[0],
                        'title': row[1],
                        'type': row[2],
                        'genres': row[3],
                        'channel_message_id': row[4]
                    }
                return None
    
    async def get_all_media(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT number, title, type, genres, channel_message_id
                FROM media ORDER BY number
            ''') as cursor:
                rows = await cursor.fetchall()
                return [{
                    'number': row[0],
                    'title': row[1],
                    'type': row[2],
                    'genres': row[3],
                    'channel_message_id': row[4]
                } for row in rows]
    
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            await db.commit()
    
    async def increment_search_count(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET search_count = search_count + 1 WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
    
    async def add_search_history(self, user_id: int, media_number: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO search_history (user_id, media_number)
                VALUES (?, ?)
            ''', (user_id, media_number))
            await db.commit()
    
    async def get_statistics(self) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            # Total users
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                total_users = (await cursor.fetchone())[0]
            
            # Total media
            async with db.execute('SELECT COUNT(*) FROM media') as cursor:
                total_media = (await cursor.fetchone())[0]
            
            # Total searches
            async with db.execute('SELECT COUNT(*) FROM search_history') as cursor:
                total_searches = (await cursor.fetchone())[0]
            
            # Media by type
            async with db.execute('''
                SELECT type, COUNT(*) FROM media GROUP BY type
            ''') as cursor:
                media_by_type = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # Top searched media
            async with db.execute('''
                SELECT m.number, m.title, COUNT(sh.id) as search_count
                FROM media m
                LEFT JOIN search_history sh ON m.number = sh.media_number
                GROUP BY m.number, m.title
                ORDER BY search_count DESC
                LIMIT 10
            ''') as cursor:
                top_searched = [{'number': row[0], 'title': row[1], 'count': row[2]} for row in await cursor.fetchall()]
            
            return {
                'total_users': total_users,
                'total_media': total_media,
                'total_searches': total_searches,
                'media_by_type': media_by_type,
                'top_searched': top_searched
            }
    
    async def delete_media(self, number: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM media WHERE number = ?', (number,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_all_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT user_id, username, first_name, last_name, joined_at, search_count
                FROM users ORDER BY joined_at DESC
            ''') as cursor:
                rows = await cursor.fetchall()
                return [{
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'joined_at': row[4],
                    'search_count': row[5]
                } for row in rows]
    
    async def add_mandatory_channel(self, channel_username: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO mandatory_channels (channel_username)
                    VALUES (?)
                ''', (channel_username,))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False
    
    async def remove_mandatory_channel(self, channel_username: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM mandatory_channels WHERE channel_username = ?', (channel_username,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_mandatory_channels(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT channel_username FROM mandatory_channels') as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
