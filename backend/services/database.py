import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "studio.sqlite3"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                background_id TEXT NOT NULL,
                video_filename TEXT NOT NULL,
                background_filename TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                processed_frames INTEGER DEFAULT 0,
                total_frames INTEGER DEFAULT 0,
                error TEXT,
                output_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def now():
    return datetime.now(timezone.utc).isoformat()


def save_asset(asset_id, asset_type, filename, path):
    with get_connection() as db:
        db.execute("""
            INSERT INTO assets (id, type, filename, path, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (asset_id, asset_type, filename, str(path), now()))


def get_asset(asset_id):
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        return dict(row) if row else None


def create_project(project):
    timestamp = now()
    with get_connection() as db:
        db.execute("""
            INSERT INTO projects (
                id, video_id, background_id,
                video_filename, background_filename,
                status, progress, processed_frames, total_frames,
                output_path, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
        """, (
            project["id"],
            project["video_id"],
            project["background_id"],
            project["video_filename"],
            project["background_filename"],
            "queued",
            project["output_path"],
            timestamp,
            timestamp
        ))


def update_project(project_id, **fields):
    allowed = {
        "status", "progress", "processed_frames", "total_frames",
        "error", "output_path"
    }
    updates = {key: value for key, value in fields.items() if key in allowed}

    if not updates:
        return

    updates["updated_at"] = now()
    assignments = ", ".join(f"{key} = ?" for key in updates)

    with get_connection() as db:
        db.execute(
            f"UPDATE projects SET {assignments} WHERE id = ?",
            (*updates.values(), project_id)
        )


def get_project(project_id):
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return dict(row) if row else None


def list_projects():
    with get_connection() as db:
        rows = db.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


init_db()


def mark_interrupted_jobs():
    timestamp = now()

    with get_connection() as db:
        cursor = db.execute("""
            UPDATE projects
            SET status = 'interrupted',
                error = 'Backend restarted while processing. Please start a new export.',
                updated_at = ?
            WHERE status IN ('queued', 'processing')
        """, (timestamp,))

        return cursor.rowcount
