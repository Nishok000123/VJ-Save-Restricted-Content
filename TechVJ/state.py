# Shared in-memory state for active forwarding jobs.
# Keyed by user_id (int).  Each value is a dict with keys:
#   link, done, total, failed, status

active_jobs: dict = {}
