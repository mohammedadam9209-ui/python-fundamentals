import os
import logging
from typing import Optional
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

# Read environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8409174359:AAF6Q3xZ_u5W60Q8QzVOHHA0hs60wsyUzJE")
AI_API_KEY = os.getenv("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")
AI_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm an AI bot. Send me a message and I'll respond.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Just send me any text message and I'll reply to it.")

async def chat_with_ai(message: str) -> Optional[str]:
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org",
        "X-Title": "Telegram AI Bot"
    }
    
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise responses."},
            {"role": "user", "content": message}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(AI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                ai_reply = data["choices"][0]["message"]["content"].strip()
                if not ai_reply:
                    return "I don't know"
                return ai_reply
            else:
                return "I don't know"
                
    except httpx.TimeoutException:
        logger.error("AI API timeout")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"AI API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"AI API error: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    
    if not user_message or not user_message.strip():
        await update.message.reply_text("Please send a text message.")
        return
    
    try:
        ai_response = await chat_with_ai(user_message)
        
        if ai_response is None:
            await update.message.reply_text("Sorry, something went wrong.")
        else:
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, something went wrong.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        try:
            await update.message.reply_text("Sorry, something went wrong.")
        except:
            pass

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
