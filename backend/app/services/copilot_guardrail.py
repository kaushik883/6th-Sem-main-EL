"""
copilot_guardrail.py — Pure-Python SQL safety validation for the Copilot.

All checks run BEFORE any database interaction. This module has zero
dependencies on SQLAlchemy, FastAPI, or the LLM SDK — it is pure stdlib.

Threat model:
- LLM prompt injection producing mutating SQL
- Comment-obfuscated mutations
- Multi-statement payloads (SQL injection via second statement)
- Cross-table access beyond the allowlist
- Sensitive column exposure (password_hash, etc.)

Returns (ok: bool, reason: str | None).
The reason is for server-side logging ONLY — never forward it to the client.
"""

import re
import logging
from typing import Optional

from app.services.copilot_schema import TABLE_ALLOWLIST, BLOCKED_COLUMNS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keywords that are never allowed in the SQL body (case-insensitive)
# ---------------------------------------------------------------------------
_MUTATION_KEYWORDS: tuple[str, ...] = (
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCOPY\b",
    r"\bCALL\b",
    r"\bMERGE\b",
    r"\bVACUUM\b",
    r"\bLOCK\b",
    r"\bUNLOCK\b",
    r"\bCOMMIT\b",
    r"\bROLLBACK\b",
    r"\bSAVEPOINT\b",
    # DO and EXECUTE are PL/pgSQL injection vectors
    r"\bDO\s+\$",        # DO $$ ... $$ style
    r"\bEXECUTE\s+",
    # SET only for session-altering usage (not SET LOCAL statement_timeout which is ours)
    r"\bSET\s+(?!LOCAL\s+statement_timeout)(?!SESSION\s+CHARACTERISTICS)",
    r"\bRESET\s+",
)

_MUTATION_RE = re.compile(
    "|".join(_MUTATION_KEYWORDS),
    re.IGNORECASE,
)

# Extract real table names from FROM / JOIN clauses.
# Skips subquery aliases by requiring the name to be followed by optional alias
# but the pattern must directly follow FROM/JOIN keywords.
# We also capture the surrounding context to skip subqueries.
_TABLE_REF_RE = re.compile(
    r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(?:AS\s+)?[a-zA-Z_][a-zA-Z0-9_]*)?",
    re.IGNORECASE,
)

# CTE alias extractor — names defined in WITH ... AS (...)
_CTE_ALIAS_RE = re.compile(
    r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
    re.IGNORECASE,
)

# Detect SQL comments
_LINE_COMMENT_RE = re.compile(r"--[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

# Subquery open parens — to detect table names after FROM inside subqueries
_SUBQUERY_FROM_RE = re.compile(r"\(\s*SELECT\b", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    """Remove -- and /* */ comments from SQL."""
    sql = _LINE_COMMENT_RE.sub(" ", sql)
    sql = _BLOCK_COMMENT_RE.sub(" ", sql)
    return sql


def _first_keyword(sql: str) -> str:
    """Return the first non-whitespace SQL token, uppercased."""
    stripped = sql.strip()
    match = re.match(r"[a-zA-Z_]+", stripped)
    return match.group(0).upper() if match else ""


def _extract_real_table_names(sql: str) -> set[str]:
    """
    Extract actual table names (not CTE aliases or subquery aliases) from SQL.

    Strategy:
    1. Find all names after FROM / JOIN.
    2. Subtract names that are CTE aliases (defined in WITH ... AS (...)).
    3. Subtract names that immediately follow a closing ) — those are
       subquery aliases (e.g. `FROM (...) AS alias`).
    """
    # Collect CTE-defined aliases so they aren't flagged as unknown tables
    cte_aliases = {m.group(1).lower() for m in _CTE_ALIAS_RE.finditer(sql)}

    # Find all FROM/JOIN targets
    raw_refs = {m.group(1).lower() for m in _TABLE_REF_RE.finditer(sql)}

    # Filter out CTE aliases — they are virtual, not real tables
    real_tables = raw_refs - cte_aliases

    # Also filter out common derived-table alias patterns:
    # Anything that follows a ) ... FROM pattern — subquery aliases.
    # Simple heuristic: if the name appears only in `AS <name>` positions
    # and never as a bare FROM target that is also in the allowlist, skip it.
    # (The allowlist check will catch any actual disallowed real tables.)
    return real_tables


def validate_sql(raw_sql: str) -> tuple[bool, Optional[str]]:
    """
    Validate LLM-generated SQL against all safety rules.

    Args:
        raw_sql: The raw SQL string from the LLM (may include markdown fences).

    Returns:
        (True, None)           — passes all checks
        (False, reason_str)    — blocked; log reason but don't expose to user
    """
    if not raw_sql or not raw_sql.strip():
        return False, "Empty SQL"

    # ── 1. Multi-statement check ─────────────────────────────────────────────
    # Strip trailing semicolon, then any remaining ; indicates multiple statements
    trimmed = raw_sql.strip().rstrip(";").strip()
    if ";" in trimmed:
        return False, f"Multi-statement SQL detected: {trimmed[:120]}"

    # ── 2. Strip comments, get the cleaned SQL ────────────────────────────────
    # We work on comment-stripped SQL for all subsequent checks.
    # Comments in LLM output are benign (we strip them), but we verify
    # that after stripping, the first real keyword is still a SELECT/WITH.
    sql = _strip_comments(trimmed).strip()

    if not sql:
        return False, "SQL was empty after stripping comments"

    # ── 3. First-keyword allowlist ───────────────────────────────────────────
    first_kw = _first_keyword(sql)
    if first_kw not in ("SELECT", "WITH", "EXPLAIN"):
        return False, f"Disallowed statement type: first keyword is '{first_kw}'"

    # EXPLAIN must wrap a SELECT
    if first_kw == "EXPLAIN":
        explain_body = re.sub(
            r"^EXPLAIN\s+(?:ANALYZE\s+)?", "", sql, flags=re.IGNORECASE
        ).strip()
        if _first_keyword(explain_body) != "SELECT":
            return False, "EXPLAIN must wrap a SELECT statement"

    # ── 4. Mutation keyword scan (on comment-stripped SQL) ───────────────────
    mutation_match = _MUTATION_RE.search(sql)
    if mutation_match:
        return False, f"Forbidden keyword detected: '{mutation_match.group(0).strip()}'"

    # ── 5. Blocked column check ──────────────────────────────────────────────
    sql_lower = sql.lower()
    for col in BLOCKED_COLUMNS:
        if col.lower() in sql_lower:
            return False, f"Blocked column reference: '{col}'"

    # ── 6. Table allowlist enforcement ───────────────────────────────────────
    referenced_tables = _extract_real_table_names(sql)
    allowlist_lower = {t.lower() for t in TABLE_ALLOWLIST}
    disallowed = referenced_tables - allowlist_lower
    if disallowed:
        return False, f"References disallowed tables: {sorted(disallowed)}"

    logger.debug("SQL guardrail passed. Tables referenced: %s", sorted(referenced_tables))
    return True, None


def extract_sql_from_llm_response(response_text: str) -> str:
    """
    Extract raw SQL from LLM response that may contain markdown code fences.
    Returns the cleaned SQL string.
    """
    text = response_text.strip()

    # Handle ```sql ... ``` or ``` ... ``` fences
    fence_match = re.search(
        r"```(?:sql)?\s*\n?(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        return fence_match.group(1).strip()

    # No fence — assume the whole response is SQL
    return text
