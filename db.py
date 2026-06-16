import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safestory.db")


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            child_age TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            pin TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_public INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            youtube_url TEXT NOT NULL,
            youtube_id TEXT NOT NULL,
            title TEXT DEFAULT '',
            thumbnail TEXT DEFAULT '',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id)
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            playlist_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(subscriber_id, playlist_id),
            FOREIGN KEY (subscriber_id) REFERENCES users(id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id)
        );
    """)
    conn.commit()
    conn.close()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _row(r):
    return dict(r) if r else None


# ── Users ──────────────────────────────────────────────────────────────────

def create_user(username, password, display_name="", child_age="", bio=""):
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password, display_name, child_age, bio) VALUES (?, ?, ?, ?, ?)",
            (username, _hash(password), display_name, child_age, bio),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str):
    conn = _conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return _row(row)


def get_user_by_id(user_id: int):
    conn = _conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _row(row)


def verify_login(username, password):
    user = get_user(username)
    if user and user["password"] == _hash(password):
        return user
    return None


def update_pin(user_id: int, pin: str):
    conn = _conn()
    conn.execute("UPDATE users SET pin = ? WHERE id = ?", (pin, user_id))
    conn.commit()
    conn.close()


def verify_pin(user_id: int, pin: str) -> bool:
    conn = _conn()
    row = conn.execute("SELECT pin FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return bool(row and row["pin"] == pin)


def update_profile(user_id: int, display_name: str, child_age: str, bio: str):
    conn = _conn()
    conn.execute(
        "UPDATE users SET display_name=?, child_age=?, bio=? WHERE id=?",
        (display_name, child_age, bio, user_id),
    )
    conn.commit()
    conn.close()


# ── Playlists ───────────────────────────────────────────────────────────────

def create_playlist(user_id: int, name: str, description: str = "", is_public: bool = False) -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO playlists (user_id, name, description, is_public) VALUES (?, ?, ?, ?)",
        (user_id, name, description, 1 if is_public else 0),
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_user_playlists(user_id: int):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM playlists WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_playlist(playlist_id: int, user_id: int):
    conn = _conn()
    conn.execute("DELETE FROM videos WHERE playlist_id = ?", (playlist_id,))
    conn.execute("DELETE FROM playlists WHERE id = ? AND user_id = ?", (playlist_id, user_id))
    conn.commit()
    conn.close()


def set_playlist_public(playlist_id: int, user_id: int, is_public: bool):
    conn = _conn()
    conn.execute(
        "UPDATE playlists SET is_public = ? WHERE id = ? AND user_id = ?",
        (1 if is_public else 0, playlist_id, user_id),
    )
    conn.commit()
    conn.close()


def get_public_playlists():
    conn = _conn()
    rows = conn.execute("""
        SELECT p.*,
               u.display_name, u.child_age, u.bio,
               (SELECT COUNT(*) FROM videos v WHERE v.playlist_id = p.id)       AS video_count,
               (SELECT COUNT(*) FROM subscriptions s WHERE s.playlist_id = p.id) AS subscriber_count
        FROM playlists p
        JOIN users u ON p.user_id = u.id
        WHERE p.is_public = 1
        ORDER BY subscriber_count DESC, p.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Videos ─────────────────────────────────────────────────────────────────

def add_video(playlist_id: int, youtube_url: str, youtube_id: str, title: str, thumbnail: str):
    conn = _conn()
    conn.execute(
        "INSERT INTO videos (playlist_id, youtube_url, youtube_id, title, thumbnail) VALUES (?, ?, ?, ?, ?)",
        (playlist_id, youtube_url, youtube_id, title, thumbnail),
    )
    conn.commit()
    conn.close()


def video_exists(playlist_id: int, youtube_id: str) -> bool:
    conn = _conn()
    row = conn.execute(
        "SELECT id FROM videos WHERE playlist_id = ? AND youtube_id = ?", (playlist_id, youtube_id)
    ).fetchone()
    conn.close()
    return row is not None


def get_playlist_videos(playlist_id: int):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM videos WHERE playlist_id = ? ORDER BY added_at DESC", (playlist_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_user_videos(user_id: int):
    conn = _conn()
    rows = conn.execute("""
        SELECT v.*, p.name AS playlist_name
        FROM videos v
        JOIN playlists p ON v.playlist_id = p.id
        WHERE p.user_id = ?
        ORDER BY v.added_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_video(video_id: int, playlist_id: int):
    conn = _conn()
    conn.execute("DELETE FROM videos WHERE id = ? AND playlist_id = ?", (video_id, playlist_id))
    conn.commit()
    conn.close()


# ── Subscriptions ───────────────────────────────────────────────────────────

def is_subscribed(subscriber_id: int, playlist_id: int) -> bool:
    conn = _conn()
    row = conn.execute(
        "SELECT id FROM subscriptions WHERE subscriber_id = ? AND playlist_id = ?",
        (subscriber_id, playlist_id),
    ).fetchone()
    conn.close()
    return row is not None


def copy_playlist(source_id: int, user_id: int, new_name: str) -> bool:
    conn = _conn()
    src = conn.execute("SELECT * FROM playlists WHERE id = ?", (source_id,)).fetchone()
    if not src:
        conn.close()
        return False

    cur = conn.execute(
        "INSERT INTO playlists (user_id, name, description) VALUES (?, ?, ?)",
        (user_id, new_name, src["description"]),
    )
    new_pid = cur.lastrowid

    videos = conn.execute("SELECT * FROM videos WHERE playlist_id = ?", (source_id,)).fetchall()
    for v in videos:
        conn.execute(
            "INSERT INTO videos (playlist_id, youtube_url, youtube_id, title, thumbnail) VALUES (?, ?, ?, ?, ?)",
            (new_pid, v["youtube_url"], v["youtube_id"], v["title"], v["thumbnail"]),
        )

    try:
        conn.execute(
            "INSERT INTO subscriptions (subscriber_id, playlist_id) VALUES (?, ?)",
            (user_id, source_id),
        )
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()
    return True
