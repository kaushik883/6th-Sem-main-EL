from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import get_password_hash
from app.models.user import Profile

router = APIRouter()

class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    company_id: int | None
    is_admin: bool
    is_active: bool

@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "forwarder", "super_admin")),
):
    if current_user["role"] == "super_admin":
        result = await db.execute(select(Profile))
    else:
        result = await db.execute(select(Profile).where(Profile.company_id == current_user["company_id"]))
    
    return result.scalars().all()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "forwarder")),
):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only company admins can add users"})

    existing = await db.execute(select(Profile).where(Profile.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Email already registered"})

    user = Profile(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name,
        password_hash=get_password_hash(body.password),
        role=current_user["role"],
        company_id=current_user["company_id"],
        is_admin=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
