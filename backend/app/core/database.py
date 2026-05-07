from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_db():
    db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_instance.db = db_instance.client[settings.MONGODB_DB]
    # Create indexes
    await db_instance.db.documents.create_index("user_id")
    await db_instance.db.documents.create_index("created_at")
    await db_instance.db.chat_sessions.create_index("document_id")

async def close_db():
    if db_instance.client:
        db_instance.client.close()

def get_db():
    return db_instance.db
