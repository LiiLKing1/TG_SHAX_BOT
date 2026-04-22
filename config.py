import os
from dotenv import load_dotenv
from config_helpers import get_env, parse_admin_ids, normalize_channel_username, validate_config, print_startup_diagnostics

# Try to load .env from multiple possible locations
load_dotenv()  # Load from current directory
load_dotenv('/app/.env')  # Load from /app directory (container path)

# Load and normalize configuration
BOT_TOKEN = get_env("BOT_TOKEN")
ADMIN_IDS = parse_admin_ids(get_env("ADMIN_IDS", ""))
CLOSED_CHANNEL_USERNAME = normalize_channel_username(get_env("CLOSED_CHANNEL_USERNAME", ""))
DATABASE_PATH = get_env("DATABASE_PATH", "bot_database.db")

# Validate configuration
config = {
    "BOT_TOKEN": BOT_TOKEN,
    "ADMIN_IDS": ADMIN_IDS,
    "CLOSED_CHANNEL_USERNAME": CLOSED_CHANNEL_USERNAME,
    "DATABASE_PATH": DATABASE_PATH
}

is_valid, errors = validate_config(config)
if not is_valid:
    print("=" * 50)
    print("CONFIGURATION ERROR")
    print("=" * 50)
    for error in errors:
        print(f"❌ {error}")
    print("=" * 50)
    raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

# Print startup diagnostics (without secrets)
print_startup_diagnostics()
