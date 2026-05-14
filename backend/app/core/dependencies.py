from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import Profile
from app.models.company import Company

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token payload"},
        )

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "User not found or inactive"},
        )

    company_name = None
    company_type = None
    if user.company_id:
        comp_result = await db.execute(select(Company).where(Company.id == user.company_id))
        company = comp_result.scalar_one_or_none()
        if company:
            company_name = company.name
            company_type = company.type

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "company_id": user.company_id,
        "company_type": company_type,
        "company_name": company_name,
        "is_admin": user.is_admin,
    }


def require_roles(*roles: str):
    """Dependency factory to restrict endpoint to specific roles."""
    async def _check(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return current_user
    return _check
