"""
copilot.py (router) — POST /api/v1/copilot/query

API contract (unchanged from stub):
  Request:  { "question": string }
  Response: { "answer": string }

Auth: JWT required, roles: client | super_admin
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.services.copilot import answer_question

router = APIRouter()


class CopilotQuery(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str


@router.post("/query", response_model=CopilotResponse)
async def ask_copilot(
    body: CopilotQuery,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
) -> CopilotResponse:
    """
    Natural-language analytics over the user's freight data.

    Generates a validated, read-only SQL query from the question, executes it
    scoped to the current user's company, and returns a plain-English summary.
    """
    answer = await answer_question(
        question=body.question,
        current_user=current_user,
        db=db,
    )
    return CopilotResponse(answer=answer)
