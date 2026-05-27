async def update_progress_message(status_msg, current: int, total: int, failed: int, link: str):
    """Edit *status_msg* with a live progress bar."""
    percent = int(current * 100 / total) if total else 100
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    text = (
        f"📥 **Batch Forward Progress**\n"
        f"[{bar}] `{percent}%`\n"
        f"✅ Done: `{current - failed}` | ❌ Failed: `{failed}` | 📦 Total: `{total}`\n"
        f"🔗 `{link}`"
    )
    try:
        await status_msg.edit_text(text)
    except Exception:
        pass


async def send_done_message(status_msg, total: int, failed: int, link: str):
    """Replace *status_msg* with the final completion summary."""
    done = total - failed
    text = (
        f"✅ **Batch Forward Complete!**\n"
        f"📦 Total: `{total}` | ✅ Sent: `{done}` | ❌ Failed: `{failed}`\n"
        f"🔗 `{link}`"
    )
    try:
        await status_msg.edit_text(text)
    except Exception:
        pass
