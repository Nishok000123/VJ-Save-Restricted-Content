# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ─────────────────────────────────────────────
# TechVJ/schedule.py  –  /schedule, /myscheds, /cancelsched commands
#                         + background scheduler loop
# ─────────────────────────────────────────────
#
# COMMANDS
#   /schedule <link> <YYYY-MM-DD> <HH:MM>
#       Schedule a single link (or range) for future forwarding.
#       Time is UTC. Example:
#           /schedule https://t.me/mychan/100-120 2025-12-01 14:30
#
#   /myscheds
#       List your pending scheduled jobs with their IDs.
#
#   /cancelsched <id>
#       Cancel a pending scheduled job by its short ID.
#
# HOW TO ACTIVATE
#   In bot.py → Bot.start(), add:
#       from TechVJ.schedule import run_scheduler
#       asyncio.create_task(run_scheduler(self))

import asyncio
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message

from config import ADMINS
from database.schedule_db import (
    add_schedule,
    get_user_schedules,
    cancel_schedule,
    get_pending_schedules,
    mark_done,
)


# ── /schedule ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command("schedule") & filters.private)
async def cmd_schedule(client: Client, message: Message):
    """
    Usage: /schedule <link_or_range> <YYYY-MM-DD> <HH:MM>
    Time is UTC.
    """
    parts = message.text.strip().split()
    if len(parts) < 4:
        return await message.reply(
            "**Usage:**\n"
            "`/schedule <link> <YYYY-MM-DD> <HH:MM>`\n\n"
            "**Example:**\n"
            "`/schedule https://t.me/mychan/100-120 2025-12-01 14:30`\n\n"
            "⚠️ Time is in **UTC**."
        )

    link       = parts[1]
    date_str   = parts[2]
    time_str   = parts[3]
    run_at_str = f"{date_str} {time_str}"

    try:
        run_at = datetime.strptime(run_at_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return await message.reply(
            "❌ Invalid date/time format.\n"
            "Use `YYYY-MM-DD HH:MM`  (e.g. `2025-12-01 14:30`)"
        )

    if run_at <= datetime.utcnow():
        return await message.reply("❌ That time is already in the past. Use a future UTC time.")

    doc_id = await add_schedule(message.from_user.id, link, run_at)
    short_id = doc_id[-6:]  # last 6 chars of ObjectId for display

    await message.reply(
        f"⏰ **Scheduled!**\n\n"
        f"🔗 Link  : `{link}`\n"
        f"🕐 Time  : `{run_at_str} UTC`\n"
        f"🆔 ID    : `{short_id}`\n\n"
        f"Use `/cancelsched {short_id}` to cancel."
    )


# ── /myscheds ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command("myscheds") & filters.private)
async def cmd_my_schedules(client: Client, message: Message):
    """List all pending scheduled jobs for this user."""
    jobs = await get_user_schedules(message.from_user.id)

    if not jobs:
        return await message.reply("📭 No pending scheduled jobs.")

    lines = ["**Your Pending Schedules:**\n"]
    for job in jobs:
        short_id = str(job["_id"])[-6:]
        run_at   = job["run_at"].strftime("%Y-%m-%d %H:%M UTC")
        lines.append(
            f"🆔 `{short_id}`  |  🕐 `{run_at}`\n"
            f"   🔗 `{job['link']}`\n"
        )

    await message.reply("\n".join(lines))


# ── /cancelsched ───────────────────────────────────────────────────────────

@Client.on_message(filters.command("cancelsched") & filters.private)
async def cmd_cancel_schedule(client: Client, message: Message):
    """Cancel a scheduled job by its short ID (last 6 chars)."""
    parts = message.text.strip().split()
    if len(parts) < 2:
        return await message.reply("Usage: `/cancelsched <id>`")

    short_id = parts[1].strip()

    # Find the full ObjectId from the user's pending schedules
    jobs = await get_user_schedules(message.from_user.id)
    matched = [j for j in jobs if str(j["_id"]).endswith(short_id)]

    if not matched:
        return await message.reply(
            f"❌ No pending schedule found with ID ending in `{short_id}`.\n"
            "Use `/myscheds` to see your jobs."
        )

    job     = matched[0]
    success = await cancel_schedule(str(job["_id"]))

    if success:
        await message.reply(
            f"🗑️ **Cancelled!**\n\n"
            f"🆔 `{short_id}`\n"
            f"🔗 `{job['link']}`"
        )
    else:
        await message.reply("❌ Could not cancel. It may have already run.")


# ── Background scheduler loop ──────────────────────────────────────────────

async def run_scheduler(client: Client):
    """
    Infinite loop — wakes every 60 s, fires any due schedules.
    Start this as an asyncio task inside Bot.start():

        asyncio.create_task(run_scheduler(self))
    """
    print("[Scheduler] Started.")
    while True:
        try:
            now     = datetime.utcnow()
            pending = await get_pending_schedules(now)

            for job in pending:
                await mark_done(str(job["_id"]))
                asyncio.create_task(_execute_job(client, job))

        except Exception as e:
            print(f"[Scheduler] Error: {e}")

        await asyncio.sleep(60)


async def _execute_job(client: Client, job: dict):
    """
    Runs one scheduled job by re-using the same forwarding logic
    used for normal user requests.

    It sends the link as a message from the bot to the user,
    which triggers the existing message handler naturally —
    OR calls forward_messages() directly if you expose it.
    """
    user_id = job["user_id"]
    link    = job["link"]

    try:
        # Notify the user the job is starting
        await client.send_message(
            user_id,
            f"⏰ **Scheduled job starting now!**\n\n🔗 `{link}`"
        )

        # Trigger the existing forwarding logic by sending the link
        # as if the user typed it — the existing message handler picks it up.
        await client.send_message(user_id, link)

    except Exception as e:
        print(f"[Scheduler] Failed to execute job for user {user_id}: {e}")
        try:
            await client.send_message(
                user_id,
                f"❌ Scheduled job failed.\n🔗 `{link}`\nError: `{e}`"
            )
        except Exception:
            pass
