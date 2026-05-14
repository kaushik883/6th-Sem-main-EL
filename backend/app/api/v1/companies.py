import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import get_password_hash
from app.models.company import Company
from app.models.user import Profile

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class CompanyOut(BaseModel):
    id: int
    name: str
    short_name: str
    type: str
    address: str | None = None
    city: str | None = None
    country: str | None = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class CreateCompanyRequest(BaseModel):
    name: str
    short_name: str
    type: str  # "client" | "forwarder"
    address: str | None = None
    city: str | None = None
    country: str | None = None
    admin_email: str
    admin_name: str
    admin_password: str


class UpdateCompanyStatusRequest(BaseModel):
    is_active: bool


# ── Helpers ────────────────────────────────────────────────────────────────────

def company_to_out(c: Company) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "short_name": c.short_name,
        "type": c.type,
        "address": c.address_line1,
        "city": c.city,
        "country": None,  # could join on countries if needed
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[CompanyOut])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List companies based on user role:
    - super_admin: sees all companies
    - forwarder: sees only client companies (to submit quotes to)
    - client: sees only forwarder companies (to receive quotes from)
    """
    query = select(Company).order_by(Company.name)
    
    # Filter based on role
    if current_user["role"] == "forwarder":
        # Forwarders see only client companies
        query = query.where(Company.type == "client", Company.is_active == True)
    elif current_user["role"] == "client":
        # Clients see only forwarder companies
        query = query.where(Company.type == "forwarder", Company.is_active == True)
    # super_admin sees all companies (no filter)
    
    result = await db.execute(query)
    companies = result.scalars().all()
    return [company_to_out(c) for c in companies]


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CreateCompanyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("super_admin")),
):
    if body.type not in ("client", "forwarder"):
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "type must be 'client' or 'forwarder'"})

    company = Company(
        name=body.name,
        short_name=body.short_name,
        type=body.type,
        address_line1=body.address,
        city=body.city,
        is_active=True,
    )
    db.add(company)
    await db.flush()  # get company.id

    # Create admin user for the company
    admin = Profile(
        id=str(uuid.uuid4()),
        email=body.admin_email,
        name=body.admin_name,
        password_hash=get_password_hash(body.admin_password),
        role=body.type,
        company_id=company.id,
        is_admin=True,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(company)
    return company_to_out(company)


@router.patch("/{company_id}/status", response_model=CompanyOut)
async def update_company_status(
    company_id: int,
    body: UpdateCompanyStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("super_admin")),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Company not found"})

    company.is_active = body.is_active
    await db.commit()
    await db.refresh(company)
    return company_to_out(company)
