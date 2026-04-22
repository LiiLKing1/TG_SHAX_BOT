from telegram import Update
from telegram.ext import ContextTypes
from database import Database

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database) -> bool:
    """Check if user is subscribed to all mandatory channels/groups"""
    mandatory_channels = await db.get_mandatory_channels()
    
    if not mandatory_channels:
        return True
    
    user_id = update.effective_user.id
    for channel in mandatory_channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Error checking subscription for {channel}: {e}")
            return False
    return True

async def send_subscription_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Send message asking user to subscribe to channels"""
    mandatory_channels = await db.get_mandatory_channels()
    
    if not mandatory_channels:
        return
    
    message = "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
    for channel in mandatory_channels:
        message += f"🔗 {channel}\n"
    message += "\nObuna bo'lgach, /start ni bosing."
    
    await update.message.reply_text(message)
