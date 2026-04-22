from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database
from admin import AdminPanel
from utils import check_subscription, send_subscription_message
from movie_helpers import handle_channel_post, handle_movie_search
from config import BOT_TOKEN, ADMIN_IDS, CLOSED_CHANNEL_USERNAME
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database and admin panel
db = Database("bot_database.db")
admin_panel = AdminPanel(db)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Check subscription
    if not await check_subscription(update, context, db):
        await send_subscription_message(update, context, db)
        return
    
    # Add user to database
    await db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Send welcome message
    welcome_message = f"""
👋 Salom, {user.first_name}!

🎬 *Kino, Multfilm va Serial Qidirish Boti*

Bu bot yordamida siz kinolarni raqam bo'yicha topishingiz mumkin.

📋 *Qanday ishlaydi:*
1. Kinoning raqamini bilib oling
2. Raqamni botga yuboring
3. Bot sizga kinoni yopiq kanaldan beradi

🔍 *Qidirish uchun:* kinoning raqamini yuboring (masalan: 1)

📞 *Yordam uchun:* /help
    """
    
    keyboard = [[InlineKeyboardButton("🔍 Qidirishni boshlash", callback_data="start_search")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
📚 *Yordam*

🔍 *Kino qidirish:*
Kinoning raqamini shunchaki yuboring. Masalan: 1, 2, 3 va hokazo.

📺 *Media turlari:*
• Kino
• Multfilm
• Serial

🔐 *Yopiq kanal:*
Barcha kinolar yopiq kanalda saqlanadi. Bot sizga kinoni shu kanaldan beradi.

⚠️ *Diqqat:*
Botdan foydalanish uchun majburiy kanallarga obuna bo'lish shart.

❓ *Savollar uchun:* admin bilan bog'laning
    """
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def search_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle media search by number (legacy - uses new movie indexing system)"""
    user = update.effective_user
    
    # Check subscription
    if not await check_subscription(update, context, db):
        await send_subscription_message(update, context, db)
        return
    
    # Get the message text (should be a number)
    text = update.message.text.strip()
    
    try:
        number = int(text)
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting!")
        return
    
    # Search for movie in new movies table
    movie = await db.find_movie_by_code(str(number))
    
    if not movie:
        await update.message.reply_text(f"❌ #{number} raqamli kino topilmadi!")
        return
    
    # Increment search count and add to history
    await db.increment_search_count(user.id)
    await db.add_search_history(user.id, number)
    
    # Get media from channel
    try:
        # Copy the message from the channel
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=movie['channel_chat_id'],
            message_id=movie['channel_message_id']
        )
        
        # Send media info in requested format
        info_message = f"""
{{ {movie['movie_code']}

[{movie['title']}]

{movie['genres']} }}
        """
        
        await update.message.reply_text(info_message)
        
    except Exception as e:
        logger.error(f"Error copying message: {e}")
        await update.message.reply_text(
            f"❌ Kinoni olishda xatolik yuz berdi.\n\n"
            f"Ma'lumot:\n"
            f"🎬 {movie['title']}\n"
            f"🎭 {movie['genres']}"
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    await admin_panel.show_admin_menu(update, context)

async def add_media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command to add media"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if len(context.args) < 5:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "Foydalanish: /add <raqam> <nom> <turi> <janrlar> <channel_message_id>\n\n"
            "Misol: /add 1 Avatar Film Action,Sci-Fi 123"
        )
        return
    
    try:
        number = int(context.args[0])
        title = ' '.join(context.args[1:-3])
        media_type = context.args[-3]
        genres = context.args[-2]
        channel_message_id = int(context.args[-1])
        
        success = await db.add_media(number, title, media_type, genres, channel_message_id)
        
        if success:
            await update.message.reply_text(f"✅ Media qo'shildi: #{number} - {title}")
        else:
            await update.message.reply_text(f"❌ #{number} raqamli media allaqachon mavjud!")
            
    except ValueError:
        await update.message.reply_text("❌ Raqam yoki message_id noto'g'ri!")

async def delete_media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete command to remove media"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "Foydalanish: /delete <raqam>\n\n"
            "Misol: /delete 1"
        )
        return
    
    try:
        number = int(context.args[0])
        success = await db.delete_media(number)
        
        if success:
            await update.message.reply_text(f"✅ #{number} raqamli media o'chirildi!")
        else:
            await update.message.reply_text(f"❌ #{number} raqamli media topilmadi!")
            
    except ValueError:
        await update.message.reply_text("❌ Raqam noto'g'ri!")

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addchannel command to add mandatory channel"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "Foydalanish: /addchannel @channelname\n\n"
            "Misol: /addchannel @mychannel"
        )
        return
    
    channel_username = context.args[0]
    success = await db.add_mandatory_channel(channel_username)
    
    if success:
        await update.message.reply_text(f"✅ Kanal qo'shildi: {channel_username}")
    else:
        await update.message.reply_text(f"❌ {channel_username} allaqachon mavjud!")

async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removechannel command to remove mandatory channel"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "Foydalanish: /removechannel @channelname\n\n"
            "Misol: /removechannel @mychannel"
        )
        return
    
    channel_username = context.args[0]
    success = await db.remove_mandatory_channel(channel_username)
    
    if success:
        await update.message.reply_text(f"✅ Kanal o'chirildi: {channel_username}")
    else:
        await update.message.reply_text(f"❌ {channel_username} topilmadi!")

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /find command to search movie by code"""
    await handle_movie_search(update, context, db)

async def movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /movie command to search movie by code"""
    await handle_movie_search(update, context, db)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command to show indexed movies count (admin only)"""
    user_id = update.effective_user.id
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    movies_count = await db.get_movies_count()
    await update.message.reply_text(f"📊 Index bo'lgan kinolar: {movies_count}")

async def reindex_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reindex_help command"""
    help_text = """
📚 *Eski kinolarni index qilish*

Bot faqat o'zi olgan `channel_post`/`edited_channel_post` update'larini index qiladi.

Eski kanal postlarini avtomatik bot API orqali scan qilmaydi.

Eski kinolarni index qilish uchun:
1. Kinolarni qayta post qiling
2. Yoki tahrirlab yangidan update tushiring

Bu usul kinolarni avtomatik ravishda index qiladi.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel posts for indexing"""
    await handle_channel_post(update, context, db, CLOSED_CHANNEL_USERNAME)

async def edited_channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edited channel posts for updating index"""
    await handle_channel_post(update, context, db, CLOSED_CHANNEL_USERNAME)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if it's an admin callback
    if user_id in ADMIN_IDS:
        await admin_panel.handle_callback(update, context)
    else:
        await query.answer("❌ Siz admin emassiz!", show_alert=True)

async def post_init(application: Application) -> None:
    """Initialize database after bot starts"""
    await db.init_db()
    logger.info("Database initialized successfully")
    logger.info(f"Target channel: {CLOSED_CHANNEL_USERNAME}")
    logger.info("Movie indexer ready")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("add", add_media_command))
    application.add_handler(CommandHandler("delete", delete_media_command))
    application.add_handler(CommandHandler("addchannel", add_channel_command))
    application.add_handler(CommandHandler("removechannel", remove_channel_command))
    application.add_handler(CommandHandler("find", find_command))
    application.add_handler(CommandHandler("movie", movie_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("reindex_help", reindex_help_command))
    
    # Handle messages (numbers for search)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, search_media))
    
    # Handle channel posts for indexing
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, channel_post_handler), group=1)
    application.add_handler(MessageHandler(filters.Caption, channel_post_handler), group=1)
    
    # Handle edited channel posts
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, edited_channel_post_handler), group=1)
    application.add_handler(MessageHandler(filters.Caption, edited_channel_post_handler), group=1)
    
    # Handle callback queries
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
