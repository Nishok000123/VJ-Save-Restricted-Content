# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# ─────────────────────────────────────────────
# state.py  –  Shared in-memory job tracker
# ─────────────────────────────────────────────
# active_jobs[user_id] = {
#     "link"   : str,
#     "done"   : int,
#     "total"  : int,
#     "failed" : int,
#     "status" : "running" | "done" | "cancelled"
# }
active_jobs: dict = {}
