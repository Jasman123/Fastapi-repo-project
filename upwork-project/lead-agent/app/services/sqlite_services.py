"""
services/sqlite_service.py
--------------------------
SQLite persistence layer.
Saves every processed lead for history, analytics, and future queries.

Schema is intentionally flat — easy to migrate to PostgreSQL later.
To migrate: swap aiosqlite → asyncpg, keep all SQL the same.
"""

import json
import aiosqlite
from datetime import datetime

from app.schemas.lead import LeadOutput
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    company_name    TEXT,
    industry        TEXT,
    location        TEXT,
    company_size    TEXT,
    contact_email   TEXT,
    score           INTEGER,
    tier            TEXT,
    score_breakdown TEXT,    -- stored as JSON string
    email_subject   TEXT,
    email_body      TEXT,
    alert_sent      INTEGER DEFAULT 0,
    sheets_row      INTEGER,
    error           TEXT,
    created_at      TEXT NOT NULL
)
"""


async def init_db() -> None:
    """
    Creates the leads table if it doesn't exist.
    Called once at app startup from main.py lifespan.
    """
    settings = get_settings()
    async with aiosqlite.connect(settings.SQLITE_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()
    logger.info(f"SQLite ready: {settings.SQLITE_PATH}")


async def save_lead_to_db(output: LeadOutput) -> int:
    """
    Inserts one lead record into SQLite.
    Returns the new row's id.
    """
    settings = get_settings()
    async with aiosqlite.connect(settings.SQLITE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO leads (
                url, company_name, industry, location, company_size,
                contact_email, score, tier, score_breakdown,
                email_subject, email_body, alert_sent, sheets_row,
                error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                output.url,
                output.company_name,
                output.industry,
                output.location,
                output.company_size,
                output.contact_email,
                output.score,
                output.tier,
                json.dumps(output.score_breakdown),
                output.email_subject,
                output.email_body,
                1 if output.alert_sent else 0,
                output.sheets_row,
                output.error,
                datetime.now().isoformat(),
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_recent_leads(limit: int = 50) -> list[dict]:
    """Returns the most recent leads for the dashboard."""
    settings = get_settings()
    async with aiosqlite.connect(settings.SQLITE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]