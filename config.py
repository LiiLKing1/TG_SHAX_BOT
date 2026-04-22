import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
CLOSED_CHANNEL_USERNAME = os.getenv("CLOSED_CHANNEL_USERNAME", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")
