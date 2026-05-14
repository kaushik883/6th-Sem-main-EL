from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, masters, companies, charges, quotes, invoices, dashboard, copilot, tracking, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix=f"{settings.API_V1_STR}/auth",      tags=["auth"])
app.include_router(masters.router,   prefix=f"{settings.API_V1_STR}/masters",   tags=["masters"])
app.include_router(companies.router, prefix=f"{settings.API_V1_STR}/companies", tags=["companies"])
app.include_router(charges.router,   prefix=f"{settings.API_V1_STR}/charges",   tags=["charges"])
app.include_router(quotes.router,    prefix=f"{settings.API_V1_STR}/quotes",    tags=["quotes"])
app.include_router(invoices.router,  prefix=f"{settings.API_V1_STR}/invoices",  tags=["invoices"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(copilot.router,   prefix=f"{settings.API_V1_STR}/copilot",   tags=["copilot"])
app.include_router(tracking.router,  prefix=f"{settings.API_V1_STR}/tracking",  tags=["tracking"])
app.include_router(users.router,     prefix=f"{settings.API_V1_STR}/users",     tags=["users"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
