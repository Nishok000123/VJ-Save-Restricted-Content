# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os

# Login feature, if you want then True , if you don't want then False
LOGIN_SYSTEM = bool(os.environ.get('LOGIN_SYSTEM', True)) # True or False

if LOGIN_SYSTEM == False:
    # if login system is False then fill your tg account session below 
    STRING_SESSION = os.environ.get("STRING_SESSION", "")
else:
    STRING_SESSION = None

# Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", ""))

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")

# Your Owner / Admin Id For Broadcast 
ADMINS = int(os.environ.get("ADMINS", "6073523936"))

# Your Channel Id In Which Bot Upload Downloaded Video/File/Message etc.
# And Make Your Bot Admin In this channel with full rights.
# if you don't want to upload in channel then leave it blank don't fill anything.
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

# Your Mongodb Database Url
# Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_URI = os.environ.get("DB_URI", "") # Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_NAME = os.environ.get("DB_NAME", "vjsavecontentbot")

# Increase time as much as possible to avoid floodwait, spamming and tg account ban issues.
WAITING_TIME = int(os.environ.get("WAITING_TIME", "10")) # time in seconds

# If You Want Error Message In Your Personal Message Then Turn It True Else If You Don't Want Then Flase
ERROR_MESSAGE = bool(os.environ.get('ERROR_MESSAGE', True))

# Force users to join this channel before using the bot.
# Set to your channel username (e.g. "@mychannel") or numeric ID (e.g. "-1001234567890").
# Leave blank to disable the force-subscribe check.
FORCE_SUB = os.environ.get("FORCE_SUB", "")

# Auto-delete messages sent by the bot after this many seconds.
# Set to 0 to disable auto-deletion.
AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "0")) # time in seconds

# Maximum number of messages allowed in a single batch request.
# Helps prevent abuse and account ban due to too many requests.
MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", "100"))

# If True, all content sent by the bot will be forward-protected (cannot be forwarded by users).
PROTECT_CONTENT = bool(os.environ.get('PROTECT_CONTENT', False))
