# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME
from datetime import datetime
from bson import ObjectId

_client = AsyncIOMotorClient(DB_URI)
_db     = _client[DB_NAME]
_col    = _db["schedules"]


async def add_schedule(user_id: int, link: str, run_at: datetime) -> str:
    result = await _col.insert_one({
        "user_id": user_id,
        "link":    link,
        "run_at":  run_at,
        "done":    False,
        "created": datetime.utcnow(),
    })
    return str(result.inserted_id)


async def get_pending_schedules(now: datetime) -> list:
    cursor = _col.find({"done": False, "run_at": {"$lte": now}})
    return await cursor.to_list(length=100)


async def get_user_schedules(user_id: int) -> list:
    cursor = _col.find({"user_id": user_id, "done": False}).sort("run_at", 1)
    return await cursor.to_list(length=50)


async def cancel_schedule(doc_id: str) -> bool:
    result = await _col.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"done": True, "cancelled": True}}
    )
    return result.modified_count > 0


async def mark_done(doc_id: str):
    await _col.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"done": True, "executed_at": datetime.utcnow()}}
    )
