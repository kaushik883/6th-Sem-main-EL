from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import Profile
from app.models.company import Company

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    company_id: int | None
    company_type: str | None
    company_name: str | None
    is_admin: bool


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid email or password"},
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid email or password"},
        )

    # Fetch company info
    company_name = None
    company_type = None
    if user.company_id:
        comp_result = await db.execute(select(Company).where(Company.id == user.company_id))
        company = comp_result.scalar_one_or_none()
        if company:
            company_name = company.name
            company_type = company.type

    token = create_access_token({"sub": user.id})

    user_out = UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        company_id=user.company_id,
        company_type=company_type,
        company_name=company_name,
        is_admin=user.is_admin,
    )

    return LoginResponse(token=token, user=user_out)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    # JWT is stateless – client drops the token
    return None


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)
