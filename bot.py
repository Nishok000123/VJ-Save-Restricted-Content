# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ─────────────────────────────────────────────
# bot.py  –  UPDATED (replace your existing bot.py with this)
# Changes vs original:
#   • Starts run_scheduler() background task on boot
#   • Keeps resume_pending_batches() call (already in your fork)
# ─────────────────────────────────────────────

import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, LOGIN_SYSTEM

if STRING_SESSION is not None and LOGIN_SYSTEM == False:
    TechVJUser = Client("TechVJ", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    TechVJUser.start()
else:
    TechVJUser = None


class Bot(Client):

    def __init__(self):
        super().__init__(
            "techvj login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=150,
            sleep_threshold=5
        )

    async def start(self):
        await super().start()

        # ── Resume any batches interrupted by a restart ──
        from TechVJ.start import resume_pending_batches
        asyncio.create_task(resume_pending_batches(self))

        # ── Start scheduled-batch background loop ──
        from TechVJ.schedule import run_scheduler
        asyncio.create_task(run_scheduler(self))

        print('Bot Started Powered By @VJ_Bots')

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')


if __name__ == "__main__":
    bot = Bot()
    bot.run()

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
