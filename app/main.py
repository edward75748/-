from __future__ import annotations

from fastapi import FastAPI

from .database import Base, engine
from .routers import accounts, advertisers, campaigns, lookups

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Campaign Management Service")

app.include_router(lookups.router, prefix="/lookups", tags=["lookups"])
app.include_router(advertisers.router, prefix="/advertisers", tags=["advertisers"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
