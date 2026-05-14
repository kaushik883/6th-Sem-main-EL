"""
copilot_executor.py — Safe async SQL execution for the Copilot.

Enforces:
- Statement timeout (Postgres SET LOCAL statement_timeout)
- Hard row cap (LIMIT wrapper)
- Read-only transaction (SET TRANSACTION READ ONLY)
- Returns list[dict] with column names preserved

This module NEVER calls the guardrail — the caller (copilot.py) is
responsible for running validate_sql() before calling execute_safe_query().
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


class CopilotQueryTimeout(Exception):
    """Raised when the query exceeds the statement timeout."""


class CopilotQueryError(Exception):
    """Raised when the query fails for any other DB reason."""


async def execute_safe_query(
    sql: str,
    db: AsyncSession,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Execute a pre-validated SELECT statement safely.

    Wraps the SQL in a LIMIT cap and enforces a statement timeout via
    Postgres session-level settings within a read-only transaction.

    Args:
        sql:  Pre-validated SQL from the guardrail (no trailing semicolon).
        db:   SQLAlchemy AsyncSession (from FastAPI dependency injection).

    Returns:
        (rows, capped) where:
          rows  — list of dicts {column_name: value}
          capped — True if the result was truncated at MAX_ROWS

    Raises:
        CopilotQueryTimeout — if Postgres statement_timeout fires
        CopilotQueryError   — for any other DB-level error
    """
    max_rows = settings.COPILOT_MAX_ROWS
    timeout_ms = settings.COPILOT_STATEMENT_TIMEOUT_MS

    # Wrap in LIMIT cap — fetch one extra row to detect truncation
    wrapped_sql = (
        f"SELECT * FROM (\n{sql}\n) AS _copilot_q"
        f" LIMIT {max_rows + 1}"
    )

    try:
        async with db.begin_nested():
            # ── Set session safety guards ────────────────────────────────────
            await db.execute(
                text(f"SET LOCAL statement_timeout = '{timeout_ms}ms'")
            )
            await db.execute(
                text("SET LOCAL transaction_read_only = on")
            )

            # ── Execute ──────────────────────────────────────────────────────
            result = await db.execute(text(wrapped_sql))
            columns = list(result.keys())
            all_rows = result.fetchall()

    except Exception as exc:
        err_str = str(exc)
        logger.error("Copilot executor DB error: %s", err_str[:400])

        if "statement_timeout" in err_str or "canceling statement" in err_str.lower():
            raise CopilotQueryTimeout("Query timed out") from exc

        raise CopilotQueryError(f"DB execution failed: {err_str[:200]}") from exc

    # Detect row cap
    capped = len(all_rows) > max_rows
    rows_to_return = all_rows[:max_rows]

    # Serialize to list[dict] — convert non-serializable types to str
    serialized: list[dict[str, Any]] = []
    for row in rows_to_return:
        record: dict[str, Any] = {}
        for col, val in zip(columns, row):
            if val is None:
                record[col] = None
            elif isinstance(val, (int, float, bool, str)):
                record[col] = val
            else:
                # Dates, Decimals, UUIDs → string
                record[col] = str(val)
        serialized.append(record)

    logger.info(
        "Copilot executor: %d rows returned (capped=%s)", len(serialized), capped
    )
    return serialized, capped
