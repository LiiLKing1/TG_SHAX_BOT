import re
import logging
from typing import Optional, Dict
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def parse_movie_caption(caption: str) -> Optional[Dict]:
    """
    Parse movie caption to extract code, title, and genres.
    
    Input example:
    "10\n\nDarsingni qil\n\n#komediya #jangari #tarjima"
    
    Returns:
        dict with keys: movie_code, title, genres, caption
        None if parsing fails
    """
    if not caption:
        return None
    
    # Split by newlines and strip each line
    lines = [line.strip() for line in caption.split('\n')]
    
    # Filter out empty lines
    meaningful_lines = [line for line in lines if line]
    
    if len(meaningful_lines) < 2:
        logger.warning(f"Caption has less than 2 meaningful lines: {caption[:50]}...")
        return None
    
    # First line is the movie code
    movie_code = meaningful_lines[0]
    
    # Validate movie code (should be numeric or alphanumeric)
    if not re.match(r'^[\w\d]+$', movie_code):
        logger.warning(f"Invalid movie code format: {movie_code}")
        return None
    
    # Second line is the title
    title = meaningful_lines[1]
    
    # Remaining lines are genres/additional info
    genres = ' '.join(meaningful_lines[2:]) if len(meaningful_lines) > 2 else ""
    
    return {
        'movie_code': movie_code,
        'title': title,
        'genres': genres,
        'caption': caption
    }

def extract_media_info(message) -> Dict:
    """
    Extract media information from a message.
    
    Returns dict with media_type and file_id
    """
    media_info = {
        'media_type': None,
        'file_id': None
    }
    
    if message.photo:
        media_info['media_type'] = 'photo'
        # Get largest photo
        media_info['file_id'] = message.photo[-1].file_id
    elif message.video:
        media_info['media_type'] = 'video'
        media_info['file_id'] = message.video.file_id
    elif message.document:
        media_info['media_type'] = 'document'
        media_info['file_id'] = message.document.file_id
    elif message.animation:
        media_info['media_type'] = 'animation'
        media_info['file_id'] = message.animation.file_id
    else:
        media_info['media_type'] = 'text'
        media_info['file_id'] = None
    
    return media_info

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE, db, target_channel: str):
    """
    Handle channel post indexing.
    
    This function indexes new or edited channel posts from the target channel.
    """
    message = update.channel_post or update.edited_channel_post
    chat_id = str(message.chat_id)
    
    # Check if this is from the target channel
    if target_channel and not target_channel.lstrip('@') in message.chat.username and chat_id != target_channel.lstrip('@'):
        return
    
    # Extract caption
    caption = message.caption or message.text or ""
    
    # Parse caption
    parsed = parse_movie_caption(caption)
    if not parsed:
        logger.info(f"Could not parse caption from channel post {message.message_id}")
        return
    
    # Extract media info
    media_info = extract_media_info(message)
    
    # Upsert to database
    success = await db.upsert_movie(
        movie_code=parsed['movie_code'],
        title=parsed['title'],
        genres=parsed['genres'],
        caption=parsed['caption'],
        channel_chat_id=chat_id,
        channel_message_id=message.message_id,
        media_type=media_info['media_type'],
        file_id=media_info['file_id']
    )
    
    if success:
        logger.info(f"Indexed movie: {parsed['movie_code']} - {parsed['title']}")
    else:
        logger.error(f"Failed to index movie: {parsed['movie_code']}")

async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    Handle user movie search by code.
    
    This function searches for a movie by code and returns the original media post.
    """
    # Get the search term
    if update.message.text:
        text = update.message.text.strip()
        
        # Check if it's a command with argument
        if text.startswith('/find ') or text.startswith('/movie '):
            search_code = text.split(' ', 1)[1].strip()
        elif text.isdigit():
            # Plain number is treated as movie code
            search_code = text
        else:
            await update.message.reply_text("Kino kodini yuboring. Masalan: 10")
            return
    else:
        await update.message.reply_text("Kino kodini yuboring. Masalan: 10")
        return
    
    # Search in database
    movie = await db.find_movie_by_code(search_code)
    
    if not movie:
        await update.message.reply_text(f"Bunday kodli kino topilmadi: {search_code}")
        return
    
    # Copy the original message from the channel
    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=movie['channel_chat_id'],
            message_id=movie['channel_message_id']
        )
        
        # Send info text
        info_text = f"🎬 {movie['title']}\nKod: {movie['movie_code']}\nJanr: {movie['genres']}"
        await update.message.reply_text(info_text)
        
    except Exception as e:
        logger.error(f"Error copying message: {e}")
        await update.message.reply_text(f"Kinoni yuborishda xatolik yuz berdi: {movie['title']}")
