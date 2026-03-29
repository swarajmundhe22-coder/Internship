from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings


def parse_sqlite_path(database_url: str) -> Path | None:
    for prefix in ("sqlite:///", "sqlite+aiosqlite:///"):
        if database_url.startswith(prefix):
            raw = database_url.replace(prefix, "", 1)
            path = Path(raw)
            return path if path.is_absolute() else (BACKEND_ROOT / path).resolve()
    return None


def run_sqlite_drill(database_path: Path, output_dir: Path) -> tuple[bool, str]:
    if not database_path.exists():
        return False, f"SQLite database file not found: {database_path}"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    backup_path = output_dir / f"sqlite_backup_{timestamp}.db"
    restore_path = output_dir / f"sqlite_restore_{timestamp}.db"

    shutil.copy2(database_path, backup_path)
    shutil.copy2(backup_path, restore_path)

    with sqlite3.connect(restore_path) as connection:
        connection.execute("SELECT 1")

    return True, f"SQLite backup+restore drill completed: backup={backup_path.name} restore={restore_path.name}"


def run_postgres_drill(database_url: str, output_dir: Path) -> tuple[bool, str]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgresql+asyncpg", "postgresql+psycopg", "postgres"}:
        return False, f"Unsupported database URL scheme for postgres drill: {parsed.scheme}"

    if shutil.which("pg_dump") is None:
        return False, "pg_dump not available in PATH"

    cli_database_url = database_url
    if database_url.startswith("postgresql+"):
        cli_database_url = "postgresql://" + database_url.split("://", 1)[1]
    elif database_url.startswith("postgres+"):
        cli_database_url = "postgres://" + database_url.split("://", 1)[1]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    backup_path = output_dir / f"postgres_backup_{timestamp}.sql"

    command = [
        "pg_dump",
        "--schema-only",
        cli_database_url,
        "-f",
        str(backup_path),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "pg_dump failed").strip()
        return False, detail

    return True, f"Postgres schema backup drill completed: backup={backup_path.name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backup and restore drill for configured database backend.")
    parser.add_argument(
        "--database-url",
        default="",
        help="Database URL to test. Defaults to Settings.database_url.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/backup_drills",
        help="Directory where drill artifacts are written.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when drill fails.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    database_url = args.database_url.strip() or get_settings().database_url

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (BACKEND_ROOT / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    sqlite_path = parse_sqlite_path(database_url)
    if sqlite_path is not None:
        passed, detail = run_sqlite_drill(sqlite_path, output_dir)
    else:
        passed, detail = run_postgres_drill(database_url, output_dir)

    print(f"Backup/restore drill status: {'PASS' if passed else 'FAIL'}")
    print(f"Detail: {detail}")

    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
