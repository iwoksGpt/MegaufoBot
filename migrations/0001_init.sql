CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  language TEXT DEFAULT 'fa',
  join_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS favorites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title_id TEXT NOT NULL,
  media_type TEXT NOT NULL,
  title TEXT NOT NULL,
  image_url TEXT,
  added_date TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, title_id, media_type)
);

CREATE TABLE IF NOT EXISTS ratings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title_id TEXT NOT NULL,
  media_type TEXT NOT NULL,
  rating INTEGER NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, title_id, media_type)
);

CREATE TABLE IF NOT EXISTS preferences (
  user_id INTEGER PRIMARY KEY,
  genres TEXT DEFAULT '[]',
  auto_update INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS statistics (
  date TEXT PRIMARY KEY,
  searches INTEGER DEFAULT 0,
  details INTEGER DEFAULT 0,
  favorites INTEGER DEFAULT 0,
  new_users INTEGER DEFAULT 0
);
