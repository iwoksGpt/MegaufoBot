import sqlite3
import json
from .config import DATABASE_FILE

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language TEXT DEFAULT 'fa',
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INTEGER PRIMARY KEY,
            favorite_genres TEXT,
            favorite_actors TEXT,
            favorite_directors TEXT,
            auto_update INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            media_id INTEGER,
            media_type TEXT,
            rating INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            media_id INTEGER,
            media_type TEXT,
            title TEXT,
            poster_path TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, media_id, media_type)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            searches INTEGER DEFAULT 0,
            recommendations INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        self.conn.commit()
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    
    def update_language(self, user_id, language):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
        self.conn.commit()
    
    def save_preferences(self, user_id, genres=None, actors=None, directors=None, auto_update=None):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            if genres is not None:
                cursor.execute("UPDATE preferences SET favorite_genres = ? WHERE user_id = ?", 
                               (json.dumps(genres), user_id))
            if actors is not None:
                cursor.execute("UPDATE preferences SET favorite_actors = ? WHERE user_id = ?", 
                               (json.dumps(actors), user_id))
            if directors is not None:
                cursor.execute("UPDATE preferences SET favorite_directors = ? WHERE user_id = ?", 
                               (json.dumps(directors), user_id))
            if auto_update is not None:
                cursor.execute("UPDATE preferences SET auto_update = ? WHERE user_id = ?", 
                               (1 if auto_update else 0, user_id))
        else:
            cursor.execute(
                "INSERT INTO preferences (user_id, favorite_genres, favorite_actors, favorite_directors, auto_update) VALUES (?, ?, ?, ?, ?)",
                (user_id, json.dumps(genres or []), json.dumps(actors or []), json.dumps(directors or []), 1 if auto_update else 0)
            )
        
        self.conn.commit()
    
    def get_preferences(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'genres': json.loads(row[1]) if row[1] else [],
                'actors': json.loads(row[2]) if row[2] else [],
                'directors': json.loads(row[3]) if row[3] else [],
                'auto_update': bool(row[4]) if row[4] is not None else False
            }
        return {'genres': [], 'actors': [], 'directors': [], 'auto_update': False}
    
    def add_rating(self, user_id, media_id, media_type, rating):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO ratings (user_id, media_id, media_type, rating) VALUES (?, ?, ?, ?)",
            (user_id, media_id, media_type, rating)
        )
        self.conn.commit()
    
    def get_ratings(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT media_id, media_type, rating FROM ratings WHERE user_id = ?", (user_id,))
        return cursor.fetchall()
    
    def update_statistics(self, search=0, recommendation=0, new_user=0):
        import datetime
        today = datetime.date.today().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM statistics WHERE date = ?", (today,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute(
                "UPDATE statistics SET searches = searches + ?, recommendations = recommendations + ?, new_users = new_users + ? WHERE date = ?",
                (search, recommendation, new_user, today)
            )
        else:
            cursor.execute(
                "INSERT INTO statistics (date, searches, recommendations, new_users) VALUES (?, ?, ?, ?)",
                (today, search, recommendation, new_user)
            )
        
        self.conn.commit()
    
    def get_statistics(self, days=7):
        import datetime
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT date, searches, recommendations, new_users FROM statistics WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date.isoformat(), end_date.isoformat())
        )
        return cursor.fetchall()
    
    def get_total_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    
    def add_to_favorites(self, user_id, media_id, media_type, title, poster_path):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO favorites (user_id, media_id, media_type, title, poster_path) VALUES (?, ?, ?, ?, ?)",
                (user_id, media_id, media_type, title, poster_path)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_from_favorites(self, user_id, media_id, media_type):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND media_id = ? AND media_type = ?",
            (user_id, media_id, media_type)
        )
        self.conn.commit()
        return cursor.rowcount > 0  # آیا حذف موفقیت‌آمیز بود؟
    
    def get_favorites(self, user_id, media_type=None):
        cursor = self.conn.cursor()
        if media_type:
            cursor.execute(
                "SELECT media_id, media_type, title, poster_path, added_date FROM favorites WHERE user_id = ? AND media_type = ? ORDER BY added_date DESC",
                (user_id, media_type)
            )
        else:
            cursor.execute(
                "SELECT media_id, media_type, title, poster_path, added_date FROM favorites WHERE user_id = ? ORDER BY added_date DESC",
                (user_id,)
            )
        return cursor.fetchall()
    
    def is_favorite(self, user_id, media_id, media_type):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND media_id = ? AND media_type = ? LIMIT 1",
            (user_id, media_id, media_type)
        )
        return cursor.fetchone() is not None
    
    def close(self):
        self.conn.close()
