"""
copilot.py — NL→SQL Copilot orchestrator service.

Pipeline:
  1. Build grounded system prompt (schema + user context + tenant rules)
  2. Call OpenAI GPT-4o-mini to generate SQL
  3. Extract & validate SQL through the guardrail
  4. Execute safely via the executor
  5. Summarize results back to natural language via a second LLM call

User-facing error messages are deliberately generic — detailed reasons are
logged server-side but never returned to the client.
"""

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.copilot_schema import SCHEMA_CONTEXT
from app.services.copilot_guardrail import validate_sql, extract_sql_from_llm_response
from app.services.copilot_executor import (
    execute_safe_query,
    CopilotQueryTimeout,
    CopilotQueryError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User-facing safe messages (never leak internals)
# ---------------------------------------------------------------------------
_MSG_NO_KEY = (
    "Copilot is not configured yet. "
    "Please add your OPENAI_API_KEY to the backend .env file and restart the server."
)
_MSG_UNSAFE = (
    "I can only answer read-only questions about your freight data. "
    "Please rephrase your question."
)
_MSG_TIMEOUT = (
    "Your query took too long to execute. "
    "Try a more specific question or narrow the date range."
)
_MSG_DB_ERROR = (
    "I encountered a database error processing your query. "
    "Please try a simpler question or contact support."
)
_MSG_NO_DATA = (
    "No data was found matching your question. "
    "The records you're asking about may not exist yet."
)
_MSG_LLM_ERROR = (
    "I had trouble generating a query for that question. "
    "Could you rephrase it or try one of the suggested queries?"
)


# ---------------------------------------------------------------------------
# OpenAI client (lazy singleton)
# ---------------------------------------------------------------------------
_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_sql_system_prompt(current_user: dict) -> str:
    role = current_user["role"]
    company_id = current_user.get("company_id")
    company_name = current_user.get("company_name") or "your company"

    tenant_rule = ""
    if role == "client" and company_id is not None:
        tenant_rule = f"""
TENANT CONTEXT (MANDATORY):
- You are answering for a CLIENT user at company_id={company_id} ({company_name}).
- Always filter quotes with: quotes.buyer_id = {company_id}
- Always filter charges/charge_aliases with: charges.company_id = {company_id}
- Always filter profiles with: profiles.company_id = {company_id}
- For invoice/anomaly queries, join through quotes to enforce buyer_id = {company_id}
- NEVER return data from other companies. This is a security requirement.
"""
    elif role == "forwarder" and company_id is not None:
        tenant_rule = f"""
TENANT CONTEXT (MANDATORY):
- You are answering for a FORWARDER user at company_id={company_id} ({company_name}).
- Always filter quotes with: quotes.forwarder_id = {company_id}
- Always filter charges/charge_aliases with: charges.company_id = {company_id}
- Always filter profiles with: profiles.company_id = {company_id}
- For invoice/anomaly queries, join through quotes to enforce forwarder_id = {company_id}
- NEVER return data from other companies. This is a security requirement.
"""
    else:
        # super_admin — sees all data, no filter injected
        tenant_rule = """
TENANT CONTEXT:
- You are answering for a SUPER ADMIN user who can see all companies' data.
- Do not add company_id filters unless the user specifically asks about a company.
"""

    return f"""You are a PostgreSQL expert generating read-only SQL for a freight audit platform.

{SCHEMA_CONTEXT}

{tenant_rule}

STRICT RULES — violating any rule causes the query to be rejected:
1. Generate ONLY a single SELECT statement (or WITH...SELECT CTE).
2. Do NOT use comments (-- or /* */) anywhere in the SQL.
3. Do NOT include INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, COPY, CALL, DO, EXECUTE, SET, RESET, COMMIT, or ROLLBACK.
4. Do NOT reference tables outside: companies, countries, currencies, airports, charges, charge_aliases, profiles, quotes, quote_charges, invoices, invoice_charges, anomalies, tracking_events.
5. Do NOT reference the column password_hash anywhere.
6. Do NOT include a trailing semicolon.
7. Return ONLY the raw SQL — no explanation, no markdown, no code fences.
8. Apply the TENANT CONTEXT filter above precisely.

If you cannot answer the question with a valid SELECT, return exactly: CANNOT_ANSWER"""


def _build_summarize_prompt(
    question: str,
    rows: list[dict[str, Any]],
    capped: bool,
) -> str:
    rows_json = json.dumps(rows[:50], indent=2, default=str)  # cap context size
    cap_note = (
        f"\n⚠️ Results were capped at {settings.COPILOT_MAX_ROWS} rows — "
        "there may be more records not shown."
        if capped
        else ""
    )
    return f"""A user asked: "{question}"

The database returned these results (JSON):
{rows_json}{cap_note}

Write a concise, professional natural-language answer to the user's question based on these results.
- Lead with the key insight or number.
- Use bullet points or a short table if there are multiple items.
- Round monetary values to 2 decimal places.
- If results are empty, say no data was found.
- Keep it under 200 words.
- Do NOT mention SQL, databases, or technical terms."""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def answer_question(
    question: str,
    current_user: dict,
    db: AsyncSession,
) -> str:
    """
    Process a natural-language question through the full NL→SQL→Answer pipeline.

    Returns a plain-English answer string safe to return to the frontend.
    Never raises — all exceptions produce a user-facing safe message.
    """

    # ── Guard: API key present ───────────────────────────────────────────────
    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
        logger.warning("Copilot called but OPENAI_API_KEY is not set")
        return _MSG_NO_KEY

    # ── Step 1: Generate SQL via OpenAI ─────────────────────────────────────
    system_prompt = _build_sql_system_prompt(current_user)

    try:
        client = _get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'Generate a PostgreSQL SELECT query to answer this question:\n"{question}"'}
            ],
            temperature=0.0,  # deterministic SQL generation
            max_tokens=1024,
        )
        raw_llm_output = response.choices[0].message.content.strip()
        logger.info(
            "Copilot LLM SQL response for user=%s: %s",
            current_user.get("id", "?"),
            raw_llm_output[:300],
        )
    except Exception as exc:
        logger.error("Copilot LLM call failed: %s", str(exc)[:300])
        return _MSG_LLM_ERROR

    # ── Step 2: Handle CANNOT_ANSWER ────────────────────────────────────────
    if raw_llm_output.strip().upper().startswith("CANNOT_ANSWER"):
        logger.info("Copilot LLM returned CANNOT_ANSWER for question: %s", question[:200])
        return _MSG_LLM_ERROR

    # ── Step 3: Extract & validate SQL ──────────────────────────────────────
    candidate_sql = extract_sql_from_llm_response(raw_llm_output)
    ok, reject_reason = validate_sql(candidate_sql)

    if not ok:
        logger.warning(
            "Copilot guardrail BLOCKED query. user=%s question=%r reason=%s sql=%r",
            current_user.get("id", "?"),
            question[:200],
            reject_reason,
            candidate_sql[:300],
        )
        return _MSG_UNSAFE

    logger.info(
        "Copilot guardrail PASSED. user=%s sql_preview=%r",
        current_user.get("id", "?"),
        candidate_sql[:200],
    )

    # ── Step 4: Execute safely ───────────────────────────────────────────────
    try:
        rows, capped = await execute_safe_query(candidate_sql, db)
    except CopilotQueryTimeout:
        logger.warning(
            "Copilot query timed out. user=%s sql=%r",
            current_user.get("id", "?"),
            candidate_sql[:200],
        )
        return _MSG_TIMEOUT
    except CopilotQueryError as exc:
        logger.error(
            "Copilot executor error. user=%s error=%s sql=%r",
            current_user.get("id", "?"),
            str(exc)[:200],
            candidate_sql[:200],
        )
        return _MSG_DB_ERROR

    # ── Step 5: Handle empty results ─────────────────────────────────────────
    if not rows:
        return _MSG_NO_DATA

    # ── Step 6: Summarize results into natural language ──────────────────────
    summarize_prompt = _build_summarize_prompt(question, rows, capped)

    try:
        summary_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": summarize_prompt}
            ],
            temperature=0.3,
            max_tokens=512,
        )
        answer = summary_response.choices[0].message.content.strip()
        logger.info(
            "Copilot answered. user=%s rows=%d capped=%s",
            current_user.get("id", "?"),
            len(rows),
            capped,
        )
        return answer
    except Exception as exc:
        logger.error("Copilot summarization LLM call failed: %s", str(exc)[:300])
        # Fallback: return a raw data dump as a safe degraded response
        preview = json.dumps(rows[:10], indent=2, default=str)
        cap_note = f"\n_(results capped at {settings.COPILOT_MAX_ROWS} rows)_" if capped else ""
        return f"Here are the results for your query:\n```\n{preview}\n```{cap_note}"
