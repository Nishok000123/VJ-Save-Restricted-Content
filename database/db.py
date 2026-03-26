# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.tasks = self.db.tasks

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
            api_id = None,
            api_hash = None,
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('session')

    async def set_api_id(self, id, api_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'api_id': api_id}})

    async def get_api_id(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('api_id')

    async def set_api_hash(self, id, api_hash):
        await self.col.update_one({'id': int(id)}, {'$set': {'api_hash': api_hash}})

    async def get_api_hash(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('api_hash')

    # ── Batch-task helpers (resume after restart) ─────────────────────────

    def new_task(self, user_id, user_chat_id, req_msg_id, url, link_type, target, from_id, to_id):
        return dict(
            user_id=int(user_id),
            user_chat_id=int(user_chat_id),
            req_msg_id=int(req_msg_id),
            url=url,
            link_type=link_type,
            target=str(target),
            from_id=int(from_id),
            to_id=int(to_id),
            current_id=int(from_id) - 1,
        )

    async def save_batch_task(self, user_id, user_chat_id, req_msg_id, url, link_type, target, from_id, to_id):
        task = self.new_task(user_id, user_chat_id, req_msg_id, url, link_type, target, from_id, to_id)
        await self.tasks.update_one(
            {'user_id': int(user_id)},
            {'$set': task},
            upsert=True,
        )

    async def update_batch_task(self, user_id, current_id):
        await self.tasks.update_one({'user_id': int(user_id)}, {'$set': {'current_id': int(current_id)}})

    async def delete_batch_task(self, user_id):
        await self.tasks.delete_many({'user_id': int(user_id)})

    async def get_all_batch_tasks(self):
        return self.tasks.find({})

db = Database(DB_URI, "TechVJDemoBot")

# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01
                                       
