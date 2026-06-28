"""
database.py — SQLite database setup and helper functions
Tables:
  - users        : registered accounts
  - submissions  : news articles submitted for analysis
  - feedback     : user feedback on results (correct / incorrect)
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "fake_news.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Users table ───────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Submissions table ──────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id              INTEGER REFERENCES users(id),
            news_title           TEXT,
            news_text            TEXT    NOT NULL,
            source_url           TEXT,
            label                TEXT    NOT NULL,  -- FAKE | REAL | UNCERTAIN
            confidence           REAL    NOT NULL,
            risk_score           INTEGER NOT NULL,
            fake_keywords        TEXT,   -- JSON list stored as string
            reliable_keywords    TEXT,   -- JSON list stored as string
            explanation          TEXT,
            submitted_at         TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Feedback table ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id  INTEGER REFERENCES submissions(id),
            user_id        INTEGER REFERENCES users(id),
            is_correct     INTEGER NOT NULL,   -- 1=correct, 0=wrong
            comment        TEXT,
            created_at     TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialized.")


# ── User helpers ───────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, password: str, email: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hash_password(password), email),
        )
        conn.commit()
        return True, "Registration successful."
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        return False, "Email already registered."
    finally:
        conn.close()


def login_user(username: str, password: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password)),
    ).fetchone()
    conn.close()
    return dict(user) if user else None


# ── Submission helpers ─────────────────────────────────────────────────────────
def save_submission(user_id, title, text, url, result: dict) -> int:
    import json
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO submissions
           (user_id, news_title, news_text, source_url,
            label, confidence, risk_score,
            fake_keywords, reliable_keywords, explanation)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, title, text, url,
            result["label"], result["confidence"], result["risk_score"],
            json.dumps(result["fake_keywords_found"]),
            json.dumps(result["reliable_keywords_found"]),
            result["explanation"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_submission(submission_id: int):
    import json
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM submissions WHERE id = ?", (submission_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["fake_keywords"]     = json.loads(d["fake_keywords"] or "[]")
    d["reliable_keywords"] = json.loads(d["reliable_keywords"] or "[]")
    return d


def get_all_submissions(user_id=None, limit=20):
    import json
    conn = get_connection()
    if user_id:
        rows = conn.execute(
            """SELECT s.*, u.username FROM submissions s
               LEFT JOIN users u ON s.user_id = u.id
               WHERE s.user_id = ?
               ORDER BY s.submitted_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT s.*, u.username FROM submissions s
               LEFT JOIN users u ON s.user_id = u.id
               ORDER BY s.submitted_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["fake_keywords"]     = json.loads(d.get("fake_keywords") or "[]")
        d["reliable_keywords"] = json.loads(d.get("reliable_keywords") or "[]")
        result.append(d)
    return result


def get_stats():
    conn = get_connection()
    total    = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
    fake     = conn.execute("SELECT COUNT(*) FROM submissions WHERE label='FAKE'").fetchone()[0]
    real     = conn.execute("SELECT COUNT(*) FROM submissions WHERE label='REAL'").fetchone()[0]
    uncertain= conn.execute("SELECT COUNT(*) FROM submissions WHERE label='UNCERTAIN'").fetchone()[0]
    users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return {"total": total, "fake": fake, "real": real, "uncertain": uncertain, "users": users}


# ── Feedback helpers ───────────────────────────────────────────────────────────
def save_feedback(submission_id, user_id, is_correct, comment=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO feedback (submission_id, user_id, is_correct, comment) VALUES (?, ?, ?, ?)",
        (submission_id, user_id, int(is_correct), comment),
    )
    conn.commit()
    conn.close()
