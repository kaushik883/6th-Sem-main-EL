from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import require_roles

router = APIRouter()


class CopilotQuery(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str


@router.post("/query", response_model=CopilotResponse)
async def ask_copilot(
    body: CopilotQuery,
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    return CopilotResponse(
        answer="Hello from LogiSight Copilot! You need to provide an OpenAI API key in .env for me to generate real SQL queries based on your data."
    )
