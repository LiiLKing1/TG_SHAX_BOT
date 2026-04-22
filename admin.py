from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from config import ADMIN_IDS
import asyncio

class AdminPanel:
    def __init__(self, db: Database):
        self.db = db
        self.broadcast_messages = {}
    
    def is_admin(self, user_id: int) -> bool:
        return user_id in ADMIN_IDS
    
    async def show_admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin menu with inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
            [InlineKeyboardButton("📺 Media Qo'shish", callback_data="add_media")],
            [InlineKeyboardButton("🗑️ Media O'chirish", callback_data="delete_media")],
            [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="users")],
            [InlineKeyboardButton("🔗 Majburiy Kanallar", callback_data="channels")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 Admin Panel\n\nQuyidagi bo'limlardan birini tanlang:",
            reply_markup=reply_markup
        )
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        stats = await self.db.get_statistics()
        
        message = "📊 *Bot Statistikasi*\n\n"
        message += f"👥 Foydalanuvchilar: {stats['total_users']}\n"
        message += f"🎬 Media: {stats['total_media']}\n"
        message += f"🔍 Qidiruvlar: {stats['total_searches']}\n\n"
        
        message += "📺 Media turi bo'yicha:\n"
        for media_type, count in stats['media_by_type'].items():
            message += f"  • {media_type}: {count}\n"
        
        message += "\n🔥 Eng ko'p qidirilgan media:\n"
        for i, item in enumerate(stats['top_searched'][:5], 1):
            message += f"  {i}. #{item['number']} - {item['title']} ({item['count']} marta)\n"
        
        await update.callback_query.message.edit_text(message, parse_mode='Markdown')
    
    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast process"""
        self.broadcast_messages[update.effective_user.id] = {'step': 'waiting_message'}
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            "📢 Broadcast yuborish\n\nYubormoqchi bo'lgan xabaringizni yozing:",
            reply_markup=reply_markup
        )
    
    async def handle_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast message"""
        user_id = update.effective_user.id
        
        if user_id not in self.broadcast_messages:
            return
        
        step = self.broadcast_messages[user_id]['step']
        
        if step == 'waiting_message':
            # Save message
            self.broadcast_messages[user_id]['message'] = update.message
            self.broadcast_messages[user_id]['step'] = 'confirmed'
            
            keyboard = [
                [InlineKeyboardButton("✅ Ha, yuborish", callback_data="confirm_broadcast")],
                [InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="cancel_broadcast")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Xabarni barcha foydalanuvchilarga yuborasizmi?",
                reply_markup=reply_markup
            )
    
    async def confirm_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and send broadcast"""
        user_id = update.effective_user.id
        
        if user_id not in self.broadcast_messages:
            return
        
        message = self.broadcast_messages[user_id]['message']
        users = await self.db.get_all_users()
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                if message.photo:
                    await message.copy(chat_id=user['user_id'])
                elif message.video:
                    await message.copy(chat_id=user['user_id'])
                elif message.document:
                    await message.copy(chat_id=user['user_id'])
                else:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=message.text
                    )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Failed to send to {user['user_id']}: {e}")
                fail_count += 1
        
        del self.broadcast_messages[user_id]
        
        await update.callback_query.message.edit_text(
            f"📢 Broadcast tugatildi!\n\n"
            f"✅ Muvaffaqiyatli: {success_count}\n"
            f"❌ Xatolik: {fail_count}"
        )
    
    async def cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel broadcast"""
        user_id = update.effective_user.id
        if user_id in self.broadcast_messages:
            del self.broadcast_messages[user_id]
        
        await self.show_admin_menu(update, context)
    
    async def show_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all users"""
        users = await self.db.get_all_users()
        
        message = "👥 *Foydalanuvchilar*\n\n"
        for user in users[:20]:  # Show first 20 users
            username = user['username'] if user['username'] else "Noma'lum"
            message += f"👤 {user['first_name']} @{username} (ID: {user['user_id']})\n"
            message += f"   Qidiruvlar: {user['search_count']}\n\n"
        
        if len(users) > 20:
            message += f"... va yana {len(users) - 20} ta foydalanuvchi"
        
        await update.callback_query.message.edit_text(message, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "stats":
            await self.show_statistics(update, context)
        elif data == "broadcast":
            await self.start_broadcast(update, context)
        elif data == "confirm_broadcast":
            await self.confirm_broadcast(update, context)
        elif data == "cancel_broadcast":
            await self.cancel_broadcast(update, context)
        elif data == "users":
            await self.show_users(update, context)
        elif data == "add_media":
            await query.message.edit_text(
                "📺 Media qo'shish uchun format:\n\n"
                "/add <raqam> <nom> <turi> <janrlar> <channel_message_id>\n\n"
                "Misol: /add 1 Avatar Film Action,Sci-Fi 123"
            )
        elif data == "delete_media":
            await query.message.edit_text(
                "🗑️ Media o'chirish uchun:\n\n"
                "/delete <raqam>\n\n"
                "Misol: /delete 1"
            )
        elif data == "channels":
            await self.show_channels(update, context)
        elif data == "back":
            await self.show_admin_menu(update, context)
    
    async def show_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show mandatory channels with management options"""
        channels = await self.db.get_mandatory_channels()
        
        if not channels:
            message = "🔗 *Majburiy Kanallar*\n\nHozircha kanallar yo'q.\n\n"
            message += "Kanal qo'shish uchun:\n/addchannel @channelname"
        else:
            message = "🔗 *Majburiy Kanallar*\n\n"
            for i, channel in enumerate(channels, 1):
                message += f"{i}. {channel}\n"
            message += "\nKanal qo'shish uchun:\n/addchannel @channelname"
            message += "\n\nKanal o'chirish uchun:\n/removechannel @channelname"
        
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)
