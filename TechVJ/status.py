# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ─────────────────────────────────────────────
# TechVJ/status.py  –  /status command
# ─────────────────────────────────────────────
#
# For regular users  →  shows their own active job (if any)
# For admins         →  also shows global stats (total active jobs, user count)
#
# Depends on:
#   TechVJ/state.py          (active_jobs dict)
#   database/users_db.py     (total_users_count — already in the original repo)
#   database/schedule_db.py  (get_user_schedules — from new schedule_db.py)

from pyrogram import Client, filters
from pyrogram.types import Message

from config import ADMINS
from TechVJ.state import active_jobs
from TechVJ.progress import make_bar
from database.schedule_db import get_user_schedules


# ── /status ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("status") & filters.private)
async def cmd_status(client: Client, message: Message):
    uid      = message.from_user.id
    is_admin = uid in (ADMINS if isinstance(ADMINS, (list, tuple, set)) else [ADMINS])
    lines    = []

    # ── Active forwarding job for this user ──
    if uid in active_jobs:
        job   = active_jobs[uid]
        bar   = make_bar(job["done"], job["total"])
        pct   = round(100 * job["done"] / job["total"]) if job["total"] else 0
        lines.append(
            f"⚙️ **Active Job**\n"
            f"🔗 `{job['link']}`\n"
            f"{bar}\n"
            f"✅ Done : `{job['done']}`  |  ❌ Failed : `{job['failed']}`  |  🔢 Total : `{job['total']}`\n"
            f"🔄 Status : `{job['status']}`"
        )
    else:
        lines.append("✅ No active forwarding job.")

    # ── Pending scheduled jobs for this user ──
    scheds = await get_user_schedules(uid)
    if scheds:
        lines.append(f"\n📅 **Pending Schedules : `{len(scheds)}`**")
        for s in scheds[:5]:                          # show max 5
            short_id = str(s["_id"])[-6:]
            run_at   = s["run_at"].strftime("%Y-%m-%d %H:%M UTC")
            lines.append(f"  🆔 `{short_id}`  🕐 `{run_at}`  🔗 `{s['link']}`")
        if len(scheds) > 5:
            lines.append(f"  … and {len(scheds) - 5} more. Use `/myscheds` to see all.")

    # ── Admin global stats ──
    if is_admin:
        # Try to import total_users_count from the original repo's users_db
        try:
            from database.users_db import total_users_count
            user_count = await total_users_count()
        except Exception:
            user_count = "N/A"

        total_active = len(active_jobs)
        lines.append(
            f"\n👑 **Admin Stats**\n"
            f"👥 Total users   : `{user_count}`\n"
            f"⚙️ Active jobs   : `{total_active}`"
        )

        # Show all active jobs (up to 10)
        if total_active > 0:
            lines.append("\n**All Active Jobs:**")
            for u_id, job in list(active_jobs.items())[:10]:
                bar = make_bar(job["done"], job["total"])
                lines.append(
                    f"  👤 `{u_id}`\n"
                    f"  {bar}\n"
                    f"  🔗 `{job['link']}`"
                )
            if total_active > 10:
                lines.append(f"  … and {total_active - 10} more.")

    await message.reply("\n".join(lines))
