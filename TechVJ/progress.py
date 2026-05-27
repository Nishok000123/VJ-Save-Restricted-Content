# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ─────────────────────────────────────────────
# TechVJ/progress.py  –  Progress bar + status message helper
# ─────────────────────────────────────────────

import math
import asyncio
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified, FloodWait


def make_bar(current: int, total: int, width: int = 12) -> str:
    """Return a text progress bar string.

    Example:  [▓▓▓▓▓░░░░░░░] 42%  (5/12)
    """
    if total <= 0:
        return f"[{'░' * width}] 0%  (0/0)"
    filled  = math.floor(width * current / total)
    empty   = width - filled
    pct     = round(100 * current / total)
    bar     = "▓" * filled + "░" * empty
    return f"[{bar}] {pct}%  ({current}/{total})"


async def update_progress_message(
    status_msg: Message,
    current: int,
    total: int,
    failed: int,
    link: str,
    extra: str = "",
) -> None:
    """Edit the status message with a live progress bar.

    Safe-wraps MessageNotModified and FloodWait.
    """
    bar  = make_bar(current, total)
    text = (
        f"📥 **Forwarding in progress...**\n"
        f"{bar}\n\n"
        f"✅ Done : `{current}`\n"
        f"❌ Failed : `{failed}`\n"
        f"🔢 Total : `{total}`\n"
        f"🔗 `{link}`"
    )
    if extra:
        text += f"\n\n{extra}"

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


async def send_done_message(
    status_msg: Message,
    total: int,
    failed: int,
    link: str,
) -> None:
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
    except MessageNotModified:
        pass
    except FloodWait as fw:
        await asyncio.sleep(fw.value)
        await status_msg.edit_text(text)
