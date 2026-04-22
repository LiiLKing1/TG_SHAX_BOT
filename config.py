import os
from dotenv import load_dotenv

# Try to load .env from multiple possible locations
load_dotenv()  # Load from current directory
load_dotenv('/app/.env')  # Load from /app directory (container path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
CLOSED_CHANNEL_USERNAME = os.getenv("CLOSED_CHANNEL_USERNAME", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

# Debug output
print(f"BOT_TOKEN loaded: {'YES' if BOT_TOKEN else 'NO'}")
print(f"BOT_TOKEN length: {len(BOT_TOKEN) if BOT_TOKEN else 0}")
print(f"ADMIN_IDS: {ADMIN_IDS}")
print(f"CLOSED_CHANNEL_USERNAME: {CLOSED_CHANNEL_USERNAME}")
