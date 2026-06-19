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
