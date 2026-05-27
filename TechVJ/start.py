# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import math
import types
import asyncio 
import pyrogram
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated,
    UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied,
    MessageNotModified
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 
from config import API_ID, API_HASH, ERROR_MESSAGE, LOGIN_SYSTEM, STRING_SESSION, CHANNEL_ID, WAITING_TIME, ADMINS
from database.db import db
from database.schedule_db import add_schedule, get_user_schedules, cancel_schedule, get_pending_schedules, mark_done
from TechVJ.strings import HELP_TXT
from bot import TechVJUser


# ── Shared state: tracks active forwarding jobs per user ─────────────────────
# active_jobs[user_id] = {"link": str, "done": int, "total": int, "failed": int, "status": str}
active_jobs: dict = {}


class batch_temp(object):
    IS_BATCH = {}


# ══════════════════════════════════════════════════════════════════════════════
# PROGRESS BAR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def make_bar(current: int, total: int, width: int = 12) -> str:
    """Return a visual progress bar string."""
    if total <= 0:
        return f"[{'░' * width}] 0%  (0/0)"
    filled = math.floor(width * current / total)
    empty  = width - filled
    pct    = round(100 * current / total)
    return f"[{'▓' * filled}{'░' * empty}] {pct}%  ({current}/{total})"


async def update_progress_msg(status_msg: Message, current: int, total: int, failed: int, link: str):
    """Edit the status message with a live progress bar. Safe — ignores no-change errors."""
    bar  = make_bar(current, total)
    text = (
        f"📥 **Forwarding in progress...**\n"
        f"{bar}\n\n"
        f"✅ Done   : `{current - failed}`\n"
        f"❌ Failed : `{failed}`\n"
        f"🔢 Total  : `{total}`\n"
        f"🔗 `{link}`"
    )
    try:
        await status_msg.edit_text(text)
    except MessageNotModified:
        pass
    except FloodWait as fw:
        await asyncio.sleep(fw.value)
        try:
            await status_msg.edit_text(text)
        except MessageNotModified:
            pass
    except Exception:
        pass


async def send_done_msg(status_msg: Message, total: int, failed: int, link: str):
    """Replace the progress message with a completion summary."""
    succeeded = total - failed
    text = (
        f"✅ **Batch Complete!**\n\n"
        f"🔗 `{link}`\n\n"
        f"📦 Total   : `{total}`\n"
        f"✅ Success : `{succeeded}`\n"
        f"❌ Failed  : `{failed}`"
    )
    try:
        await status_msg.edit_text(text)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD / UPLOAD STATUS (original helpers — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

async def downstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Downloaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


async def upstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Uploaded:** **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


# ══════════════════════════════════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url="https://t.me/kingvj01")
    ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_bots')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id,
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot, I can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )


# ══════════════════════════════════════════════════════════════════════════════
# /help
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(chat_id=message.chat.id, text=f"{HELP_TXT}")


# ══════════════════════════════════════════════════════════════════════════════
# /cancel
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await db.delete_batch_task(message.from_user.id)
    active_jobs.pop(message.from_user.id, None)
    await client.send_message(chat_id=message.chat.id, text="**Batch Successfully Cancelled.**")


# ══════════════════════════════════════════════════════════════════════════════
# /status  — shows active job progress + pending schedules
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["status"]) & filters.private)
async def cmd_status(client: Client, message: Message):
    uid      = message.from_user.id
    is_admin = uid in (ADMINS if isinstance(ADMINS, (list, tuple, set)) else [ADMINS])
    lines    = []

    # Active forwarding job
    if uid in active_jobs:
        job     = active_jobs[uid]
        current = job["done"] + job["failed"]
        bar     = make_bar(current, job["total"])
        lines.append(
            f"⚙️ **Active Job**\n"
            f"🔗 `{job['link']}`\n"
            f"{bar}\n"
            f"✅ Done : `{job['done']}`  ❌ Failed : `{job['failed']}`  🔢 Total : `{job['total']}`\n"
            f"🔄 Status : `{job['status']}`"
        )
    else:
        lines.append("✅ No active forwarding job.")

    # Pending scheduled jobs
    scheds = await get_user_schedules(uid)
    if scheds:
        lines.append(f"\n📅 **Pending Schedules : `{len(scheds)}`**")
        for s in scheds[:5]:
            short_id = str(s["_id"])[-6:]
            run_at   = s["run_at"].strftime("%Y-%m-%d %H:%M UTC")
            lines.append(f"  🆔 `{short_id}`  🕐 `{run_at}`\n  🔗 `{s['link']}`")
        if len(scheds) > 5:
            lines.append(f"  … and {len(scheds) - 5} more. Use /myscheds to see all.")

    # Admin global stats
    if is_admin:
        try:
            user_count = await db.total_users_count()
        except Exception:
            user_count = "N/A"
        total_active = len(active_jobs)
        lines.append(
            f"\n👑 **Admin Stats**\n"
            f"👥 Total users  : `{user_count}`\n"
            f"⚙️ Active jobs  : `{total_active}`"
        )
        if total_active > 0:
            lines.append("\n**All Active Jobs:**")
            for u_id, job in list(active_jobs.items())[:10]:
                current = job["done"] + job["failed"]
                bar     = make_bar(current, job["total"])
                lines.append(f"  👤 `{u_id}`\n  {bar}\n  🔗 `{job['link']}`")
            if total_active > 10:
                lines.append(f"  … and {total_active - 10} more.")

    await message.reply("\n".join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# /schedule  — schedule a batch for later
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["schedule"]) & filters.private)
async def cmd_schedule(client: Client, message: Message):
    """
    Usage: /schedule <link> <YYYY-MM-DD> <HH:MM>
    Time is UTC.
    Example: /schedule https://t.me/mychan/100-120 2025-12-01 14:30
    """
    parts = message.text.strip().split()
    if len(parts) < 4:
        return await message.reply(
            "**Usage:**\n"
            "`/schedule <link> <YYYY-MM-DD> <HH:MM>`\n\n"
            "**Example:**\n"
            "`/schedule https://t.me/mychan/100-120 2025-12-01 14:30`\n\n"
            "⚠️ Time is **UTC**."
        )

    link       = parts[1]
    run_at_str = f"{parts[2]} {parts[3]}"

    try:
        run_at = datetime.strptime(run_at_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return await message.reply(
            "❌ Invalid date/time format.\n"
            "Use `YYYY-MM-DD HH:MM`  e.g. `2025-12-01 14:30`"
        )

    if run_at <= datetime.utcnow():
        return await message.reply("❌ That time is already in the past. Use a future UTC time.")

    doc_id   = await add_schedule(message.from_user.id, link, run_at)
    short_id = doc_id[-6:]

    await message.reply(
        f"⏰ **Scheduled!**\n\n"
        f"🔗 Link  : `{link}`\n"
        f"🕐 Time  : `{run_at_str} UTC`\n"
        f"🆔 ID    : `{short_id}`\n\n"
        f"Use `/cancelsched {short_id}` to cancel."
    )


# ══════════════════════════════════════════════════════════════════════════════
# /myscheds  — list pending scheduled jobs
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["myscheds"]) & filters.private)
async def cmd_my_schedules(client: Client, message: Message):
    jobs = await get_user_schedules(message.from_user.id)
    if not jobs:
        return await message.reply("📭 No pending scheduled jobs.")

    lines = ["**Your Pending Schedules:**\n"]
    for job in jobs:
        short_id = str(job["_id"])[-6:]
        run_at   = job["run_at"].strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"🆔 `{short_id}`  🕐 `{run_at}`\n   🔗 `{job['link']}`\n")

    await message.reply("\n".join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# /cancelsched  — cancel a scheduled job
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command(["cancelsched"]) & filters.private)
async def cmd_cancel_schedule(client: Client, message: Message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        return await message.reply("Usage: `/cancelsched <id>`")

    short_id = parts[1].strip()
    jobs     = await get_user_schedules(message.from_user.id)
    matched  = [j for j in jobs if str(j["_id"]).endswith(short_id)]

    if not matched:
        return await message.reply(
            f"❌ No pending schedule with ID ending in `{short_id}`.\n"
            "Use /myscheds to see your jobs."
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


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MESSAGE HANDLER  (handles all t.me links)
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    # ── Join chat via invite link ─────────────────────────────────────────
    if ("https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text) and LOGIN_SYSTEM == False:
        if TechVJUser is None:
            await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return
        try:
            try:
                await TechVJUser.join_chat(message.text)
            except Exception as e:
                await client.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)
                return
            await client.send_message(message.chat.id, "Chat Joined", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await client.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
        except InviteHashExpired:
            await client.send_message(message.chat.id, "Invalid Link", reply_to_message_id=message.id)
        return

    # ── Forward link ──────────────────────────────────────────────────────
    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")

        datas  = message.text.split("/")
        temp   = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        # ── Auth / session setup ──────────────────────────────────────────
        if LOGIN_SYSTEM == True:
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id   = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            except:
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
        else:
            if TechVJUser is None:
                await client.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
                return
            acc = TechVJUser

        batch_temp.IS_BATCH[message.from_user.id] = False

        # ── Save task to DB for resume support ────────────────────────────
        if "https://t.me/c/" in message.text:
            link_type   = 'private'
            link_target = "-100" + datas[4]
        elif "https://t.me/b/" in message.text:
            link_type   = 'bot'
            link_target = datas[4]
        else:
            link_type   = 'public'
            link_target = datas[3]

        await db.save_batch_task(
            message.from_user.id, message.chat.id, message.id,
            message.text, link_type, link_target, fromID, toID
        )

        # ── Register in active_jobs for /status ───────────────────────────
        total = toID - fromID + 1
        link  = message.text
        active_jobs[message.from_user.id] = {
            "link":   link,
            "done":   0,
            "total":  total,
            "failed": 0,
            "status": "running",
        }

        # ── Send initial progress message ─────────────────────────────────
        status_msg = await message.reply(
            f"📥 **Starting batch...**\n"
            f"{make_bar(0, total)}\n\n"
            f"🔢 Total : `{total}` messages\n"
            f"🔗 `{link}`"
        )

        done   = 0
        failed = 0

        # ── Main forwarding loop ──────────────────────────────────────────
        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id):
                break

            success = True

            # private / bot
            if "https://t.me/c/" in message.text or "https://t.me/b/" in message.text:
                if "https://t.me/c/" in message.text:
                    chatid = int("-100" + datas[4])
                else:
                    chatid = datas[4]
                try:
                    await handle_private(client, acc, message, chatid, msgid)
                except Exception as e:
                    success = False
                    if ERROR_MESSAGE:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # public
            else:
                username = datas[3]
                if CHANNEL_ID:
                    try:
                        pub_chat = int(CHANNEL_ID)
                    except ValueError:
                        pub_chat = CHANNEL_ID
                else:
                    pub_chat = message.chat.id
                reply_id = message.id if pub_chat == message.chat.id else None

                try:
                    msg = await client.get_messages(username, msgid)
                except UsernameNotOccupied:
                    await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                    break
                try:
                    await client.copy_message(pub_chat, msg.chat.id, msg.id, reply_to_message_id=reply_id)
                except:
                    try:
                        await handle_private(client, acc, message, username, msgid)
                    except Exception as e:
                        success = False
                        if ERROR_MESSAGE:
                            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # ── Update counters ───────────────────────────────────────────
            if success:
                done += 1
            else:
                failed += 1

            active_jobs[message.from_user.id]["done"]   = done
            active_jobs[message.from_user.id]["failed"] = failed

            # ── Refresh progress bar every 5 messages or on last ──────────
            current = done + failed
            if current % 5 == 0 or current == total:
                await update_progress_msg(status_msg, current, total, failed, link)

            # ── Update DB for resume support ──────────────────────────────
            await db.update_batch_task(message.from_user.id, msgid)

            await asyncio.sleep(WAITING_TIME)

        # ── Cleanup ───────────────────────────────────────────────────────
        if LOGIN_SYSTEM == True:
            try:
                await acc.disconnect()
            except:
                pass

        active_jobs.pop(message.from_user.id, None)
        batch_temp.IS_BATCH[message.from_user.id] = True
        await db.delete_batch_task(message.from_user.id)

        # ── Final summary ─────────────────────────────────────────────────
        await send_done_msg(status_msg, total, failed, link)


# ══════════════════════════════════════════════════════════════════════════════
# HANDLE PRIVATE  (original — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty: return
    msg_type = get_message_type(msg)
    if not msg_type: return
    if CHANNEL_ID:
        try:
            chat = int(CHANNEL_ID)
        except:
            chat = message.chat.id
    else:
        chat = message.chat.id
    if batch_temp.IS_BATCH.get(message.from_user.id): return
    if "Text" == msg_type:
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return

    smsg = await client.send_message(message.chat.id, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if ERROR_MESSAGE:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        return await smsg.delete()
    if batch_temp.IS_BATCH.get(message.from_user.id): return
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))

    caption = msg.caption if msg.caption else None
    if batch_temp.IS_BATCH.get(message.from_user.id): return

    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path is not None: os.remove(ph_path)

    elif "Video" == msg_type:
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path is not None: os.remove(ph_path)

    elif "Animation" == msg_type:
        try:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    elif "Sticker" == msg_type:
        try:
            await client.send_sticker(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    elif "Voice" == msg_type:
        try:
            await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    elif "Audio" == msg_type:
        try:
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path is not None: os.remove(ph_path)

    elif "Photo" == msg_type:
        try:
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    await client.delete_messages(message.chat.id, [smsg.id])


# ══════════════════════════════════════════════════════════════════════════════
# GET MESSAGE TYPE  (original — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except: pass
    try:
        msg.video.file_id
        return "Video"
    except: pass
    try:
        msg.animation.file_id
        return "Animation"
    except: pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except: pass
    try:
        msg.voice.file_id
        return "Voice"
    except: pass
    try:
        msg.audio.file_id
        return "Audio"
    except: pass
    try:
        msg.photo.file_id
        return "Photo"
    except: pass
    try:
        msg.text
        return "Text"
    except: pass


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER BACKGROUND LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def run_scheduler(client: Client):
    """
    Infinite background loop — wakes every 60 s, fires any due schedules.
    Start this in bot.py → Bot.start():
        from TechVJ.start import run_scheduler
        asyncio.create_task(run_scheduler(self))
    """
    print("[Scheduler] Started.")
    while True:
        try:
            now     = datetime.utcnow()
            pending = await get_pending_schedules(now)
            for job in pending:
                await mark_done(str(job["_id"]))
                asyncio.create_task(_execute_scheduled_job(client, job))
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
        await asyncio.sleep(60)


async def _execute_scheduled_job(client: Client, job: dict):
    """
    Runs one scheduled job by sending the link to the user —
    the existing save() handler picks it up automatically.
    """
    user_id = job["user_id"]
    link    = job["link"]
    try:
        await client.send_message(
            user_id,
            f"⏰ **Scheduled job starting now!**\n\n🔗 `{link}`"
        )
        # Send the link as a normal message — save() handles it
        await client.send_message(user_id, link)
    except Exception as e:
        print(f"[Scheduler] Job failed for user {user_id}: {e}")
        try:
            await client.send_message(
                user_id,
                f"❌ Scheduled job failed.\n🔗 `{link}`\nError: `{e}`"
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# RESUME PENDING BATCHES ON BOT RESTART  (original — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

async def resume_pending_batches(client: Client):
    """Called on bot startup to resume any interrupted batch tasks."""
    try:
        pending = await db.get_all_batch_tasks()
    except Exception:
        return
    async for task in pending:
        asyncio.create_task(_resume_batch(client, task))


async def _resume_batch(client: Client, task: dict):
    """Process the remaining messages of a single interrupted batch task."""
    user_id      = task['user_id']
    user_chat_id = task['user_chat_id']
    req_msg_id   = task.get('req_msg_id', 0)
    url          = task['url']
    link_type    = task['link_type']
    target       = task['target']
    from_id      = task['from_id']
    to_id        = task['to_id']
    current_id   = task.get('current_id', from_id - 1)

    resume_from = current_id + 1
    if resume_from > to_id:
        await db.delete_batch_task(user_id)
        return

    try:
        await client.send_message(
            user_chat_id,
            f"**🔄 Bot restarted. Resuming your batch task from message {resume_from} to {to_id}...**"
        )
    except Exception:
        pass

    if LOGIN_SYSTEM == True:
        user_data = await db.get_session(user_id)
        if user_data is None:
            await db.delete_batch_task(user_id)
            try:
                await client.send_message(user_chat_id, "**❌ Session expired. Cannot resume batch. Please start again.**")
            except Exception:
                pass
            return
        try:
            api_id   = int(await db.get_api_id(user_id))
            api_hash = await db.get_api_hash(user_id)
            acc      = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
            await acc.connect()
        except Exception as e:
            await db.delete_batch_task(user_id)
            try:
                await client.send_message(user_chat_id, f"**❌ Cannot resume batch. Login error: {e}**")
            except Exception:
                pass
            return
    else:
        if TechVJUser is None:
            await db.delete_batch_task(user_id)
            return
        acc = TechVJUser

    fake_msg = types.SimpleNamespace(
        id=req_msg_id,
        from_user=types.SimpleNamespace(id=user_id),
        chat=types.SimpleNamespace(id=user_chat_id),
        text=url,
    )

    batch_temp.IS_BATCH[user_id] = False

    # Register resumed job in active_jobs
    total = to_id - resume_from + 1
    active_jobs[user_id] = {
        "link":   url,
        "done":   0,
        "total":  total,
        "failed": 0,
        "status": "resumed",
    }

    # Send progress message for resumed batch
    try:
        status_msg = await client.send_message(
            user_chat_id,
            f"📥 **Resuming batch...**\n"
            f"{make_bar(0, total)}\n\n"
            f"🔢 Total remaining : `{total}`\n"
            f"🔗 `{url}`"
        )
        show_progress = True
    except Exception:
        show_progress = False

    done   = 0
    failed = 0

    for msgid in range(resume_from, to_id + 1):
        if batch_temp.IS_BATCH.get(user_id):
            break

        success = True

        if link_type == 'private':
            try:
                await handle_private(client, acc, fake_msg, int(target), msgid)
            except Exception as e:
                success = False
                if ERROR_MESSAGE:
                    try:
                        await client.send_message(user_chat_id, f"Error: {e}")
                    except Exception:
                        pass

        elif link_type == 'bot':
            try:
                await handle_private(client, acc, fake_msg, target, msgid)
            except Exception as e:
                success = False
                if ERROR_MESSAGE:
                    try:
                        await client.send_message(user_chat_id, f"Error: {e}")
                    except Exception:
                        pass

        else:  # public
            if CHANNEL_ID:
                try:
                    pub_chat = int(CHANNEL_ID)
                except ValueError:
                    pub_chat = CHANNEL_ID
            else:
                pub_chat = user_chat_id
            try:
                msg = await client.get_messages(target, msgid)
                try:
                    await client.copy_message(pub_chat, msg.chat.id, msg.id)
                except Exception:
                    try:
                        await handle_private(client, acc, fake_msg, target, msgid)
                    except Exception as e:
                        success = False
                        if ERROR_MESSAGE:
                            try:
                                await client.send_message(user_chat_id, f"Error: {e}")
                            except Exception:
                                pass
            except Exception as e:
                success = False
                if ERROR_MESSAGE:
                    try:
                        await client.send_message(user_chat_id, f"Error: {e}")
                    except Exception:
                        pass

        if success:
            done += 1
        else:
            failed += 1

        active_jobs[user_id]["done"]   = done
        active_jobs[user_id]["failed"] = failed

        current = done + failed
        if show_progress and (current % 5 == 0 or current == total):
            try:
                await update_progress_msg(status_msg, current, total, failed, url)
            except Exception:
                pass

        await db.update_batch_task(user_id, msgid)
        await asyncio.sleep(WAITING_TIME)

    if LOGIN_SYSTEM == True:
        try:
            await acc.disconnect()
        except Exception:
            pass

    active_jobs.pop(user_id, None)
    batch_temp.IS_BATCH[user_id] = True
    await db.delete_batch_task(user_id)

    try:
        if show_progress:
            await send_done_msg(status_msg, total, failed, url)
        await client.send_message(user_chat_id, "**✅ Resumed batch task completed.**")
    except Exception:
        pass


# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01
