"""SQLite persistence for user-owned error records and bookmarked references."""
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "code_doctor.db"

@contextmanager
def connect(path=None):
    conn = sqlite3.connect(str(path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize(path=None):
    with connect(path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS error_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'python',
                environment TEXT NOT NULL DEFAULT '',
                error_type TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT '',
                source_code TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                expected TEXT NOT NULL DEFAULT '',
                actual TEXT NOT NULL DEFAULT '',
                cause TEXT NOT NULL DEFAULT '',
                solution TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '미해결'
                    CHECK (status IN ('미해결', '해결 중', '해결')),
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id INTEGER NOT NULL REFERENCES error_records(id) ON DELETE CASCADE,
                question_id INTEGER NOT NULL,
                answer_id INTEGER,
                question_title TEXT NOT NULL,
                question_url TEXT NOT NULL,
                added_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                UNIQUE(error_id, question_id, answer_id)
            );
            CREATE TABLE IF NOT EXISTS translation_cache (
                fingerprint TEXT NOT NULL,
                target_language TEXT NOT NULL,
                translated TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                PRIMARY KEY(fingerprint, target_language)
            );
        """)


def create_error(fields, path=None):
    cols = ("title", "language", "environment", "error_type", "error_message", "source_code",
            "description", "expected", "actual", "cause", "solution", "status")
    data = [fields.get(col, "") for col in cols]
    if not str(data[0]).strip():
        raise ValueError("오류 제목을 입력하세요.")
    with connect(path) as conn:
        cur = conn.execute(f"INSERT INTO error_records ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", data)
        return cur.lastrowid


def list_errors(search="", status="전체", path=None):
    sql = "SELECT * FROM error_records WHERE 1=1"
    params = []
    if search.strip():
        sql += " AND (title LIKE ? OR error_type LIKE ? OR error_message LIKE ? OR solution LIKE ?)"
        term = "%" + search.strip() + "%"
        params.extend([term] * 4)
    if status != "전체":
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY updated_at DESC, id DESC"
    with connect(path) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_error(record_id, path=None):
    with connect(path) as conn:
        row = conn.execute("SELECT * FROM error_records WHERE id=?", (record_id,)).fetchone()
        return dict(row) if row else None


def update_error(record_id, fields, path=None):
    allowed = ("title", "status", "cause", "solution", "description", "expected", "actual")
    values = {k: v for k, v in fields.items() if k in allowed}
    if not values:
        return False
    with connect(path) as conn:
        cursor = conn.execute(
            "UPDATE error_records SET " + ", ".join(f"{k}=?" for k in values)
            + ", updated_at=datetime('now','localtime') WHERE id=?",
            [*values.values(), record_id],
        )
        return cursor.rowcount > 0


def delete_error(record_id, path=None):
    with connect(path) as conn:
        cursor = conn.execute("DELETE FROM error_records WHERE id=?", (record_id,))
        return cursor.rowcount > 0


def add_bookmark(error_id, question, answer=None, path=None):
    question_id = int(question["question_id"])
    answer_id = int(answer["answer_id"]) if answer else None
    with connect(path) as conn:
        existing = conn.execute("""
            SELECT id FROM bookmarks WHERE error_id=? AND question_id=? AND answer_id IS ?
        """, (error_id, question_id, answer_id)).fetchone()
        if existing:
            return False
        conn.execute("""INSERT INTO bookmarks
            (error_id, question_id, answer_id, question_title, question_url)
            VALUES (?, ?, ?, ?, ?)""",
            (error_id, question_id, answer_id, question.get("title", ""), question.get("link", "")))
    return True


def list_bookmarks(error_id, path=None):
    with connect(path) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM bookmarks WHERE error_id=? ORDER BY id DESC", (error_id,)
        ).fetchall()]


def _fingerprint(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def get_translation(source, language, path=None):
    with connect(path) as conn:
        row = conn.execute("SELECT translated FROM translation_cache WHERE fingerprint=? AND target_language=?",
                           (_fingerprint(source), language)).fetchone()
        return row["translated"] if row else None


def save_translation(source, language, translated, path=None):
    with connect(path) as conn:
        conn.execute("INSERT OR REPLACE INTO translation_cache (fingerprint,target_language,translated) VALUES (?,?,?)",
                     (_fingerprint(source), language, translated))


def statistics(path=None):
    with connect(path) as conn:
        statuses = [dict(r) for r in conn.execute(
            "SELECT status,COUNT(*) AS count FROM error_records GROUP BY status").fetchall()]
        categories = [dict(r) for r in conn.execute(
            "SELECT CASE WHEN error_type='' THEN '기타' ELSE error_type END AS error_type,COUNT(*) AS count FROM error_records GROUP BY 1 ORDER BY count DESC").fetchall()]
    return statuses, categories
