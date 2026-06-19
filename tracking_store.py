import sqlite3
import time
import os

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracking.db')


def _conn():
    c = sqlite3.connect(_DB, check_same_thread=False)
    c.execute('''CREATE TABLE IF NOT EXISTS tracks
                 (token TEXT PRIMARY KEY,
                  dest_url TEXT NOT NULL,
                  chat_id INTEGER NOT NULL,
                  created_at REAL NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_stats
                 (group_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  username TEXT,
                  full_name TEXT,
                  msg_count INTEGER DEFAULT 0,
                  PRIMARY KEY (group_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats
                 (group_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  username TEXT,
                  full_name TEXT,
                  day_count INTEGER DEFAULT 0,
                  stat_date TEXT NOT NULL,
                  PRIMARY KEY (group_id, user_id, stat_date))''')
    c.commit()
    return c


def save(token: str, dest_url: str, chat_id: int):
    with _conn() as c:
        c.execute('INSERT OR REPLACE INTO tracks VALUES (?,?,?,?)',
                  (token, dest_url, int(chat_id), time.time()))


def get(token: str):
    with _conn() as c:
        return c.execute(
            'SELECT dest_url, chat_id FROM tracks WHERE token=?', (token,)
        ).fetchone()


def stats_artir(group_id: int, user_id: int, username: str, full_name: str):
    today = _today()
    with _conn() as c:
        c.execute('''INSERT INTO group_stats (group_id, user_id, username, full_name, msg_count)
                     VALUES (?,?,?,?,1)
                     ON CONFLICT(group_id, user_id) DO UPDATE SET
                         msg_count = msg_count + 1,
                         username = excluded.username,
                         full_name = excluded.full_name''',
                  (int(group_id), int(user_id), username or '', full_name or ''))
        c.execute('''INSERT INTO daily_stats (group_id, user_id, username, full_name, day_count, stat_date)
                     VALUES (?,?,?,?,1,?)
                     ON CONFLICT(group_id, user_id, stat_date) DO UPDATE SET
                         day_count = day_count + 1,
                         username = excluded.username,
                         full_name = excluded.full_name''',
                  (int(group_id), int(user_id), username or '', full_name or '', today))


def stats_getir(group_id: int, limit: int = 10):
    with _conn() as c:
        return c.execute(
            '''SELECT user_id, username, full_name, msg_count
               FROM group_stats WHERE group_id=?
               ORDER BY msg_count DESC LIMIT ?''',
            (int(group_id), limit)
        ).fetchall()


def stats_toplam(group_id: int) -> int:
    with _conn() as c:
        row = c.execute(
            'SELECT SUM(msg_count) FROM group_stats WHERE group_id=?',
            (int(group_id),)
        ).fetchone()
        return row[0] or 0


def daily_stats_getir(group_id: int, tarih: str = None, limit: int = 10):
    tarih = tarih or _today()
    with _conn() as c:
        return c.execute(
            '''SELECT user_id, username, full_name, day_count
               FROM daily_stats WHERE group_id=? AND stat_date=?
               ORDER BY day_count DESC LIMIT ?''',
            (int(group_id), tarih, limit)
        ).fetchall()


def stats_tum_gruplar():
    with _conn() as c:
        return [row[0] for row in c.execute(
            'SELECT DISTINCT group_id FROM group_stats'
        ).fetchall()]


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()
