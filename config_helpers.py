import os
import sys
import re
from typing import Optional, List

def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default value."""
    return os.getenv(key, default)

def parse_admin_ids(admin_ids_str: str) -> List[int]:
    """Parse admin IDs from comma-separated string."""
    return [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

def normalize_channel_username(channel: str) -> str:
    """
    Normalize channel username to @username format.
    
    Examples:
        "https://t.me/fhfjucucuccuucuc" -> "@fhfjucucuccuucuc"
        "fhfjucucuccuucuc" -> "@fhfjucucuccuucuc"
        "@fhfjucucuccuucuc" -> "@fhfjucucuccuucuc"
    """
    if not channel:
        return ""
    
    # Remove whitespace
    channel = channel.strip()
    
    # If starts with @, already normalized
    if channel.startswith("@"):
        return channel
    
    # If it's a URL, extract username
    if "t.me/" in channel:
        match = re.search(r"t\.me/([^/?]+)", channel)
        if match:
            return f"@{match.group(1)}"
    
    # Otherwise, just add @ prefix
    return f"@{channel}"

def validate_config(config: dict) -> tuple[bool, List[str]]:
    """
    Validate configuration.
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    if not config.get("BOT_TOKEN"):
        errors.append("BOT_TOKEN is required")
    elif len(config["BOT_TOKEN"]) < 30:
        errors.append("BOT_TOKEN appears to be invalid (too short)")
    
    if not config.get("ADMIN_IDS"):
        errors.append("ADMIN_IDS is required")
    elif not isinstance(config["ADMIN_IDS"], list):
        errors.append("ADMIN_IDS must be a list of integers")
    
    if not config.get("CLOSED_CHANNEL_USERNAME"):
        errors.append("CLOSED_CHANNEL_USERNAME is required")
    
    return len(errors) == 0, errors

def print_startup_diagnostics():
    """Print startup diagnostics (without secrets)."""
    import telegram
    
    print("=" * 50)
    print("STARTUP DIAGNOSTICS")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"python-telegram-bot version: {telegram.__version__}")
    print(f"Runtime mode: {'Production' if os.getenv('RAILWAY_ENVIRONMENT') else 'Development'}")
    print("=" * 50)
