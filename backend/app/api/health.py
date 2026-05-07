from fastapi import APIRouter
from app.core.database import db_instance

router = APIRouter()

@router.get("/health")
async def health():
    try:
        await db_instance.client.admin.command("ping")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": "connected" if db_ok else "disconnected"}
