import asyncio
from io import BytesIO
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests

load_dotenv(verbose=True, dotenv_path=".env.local")
load_dotenv(verbose=True, dotenv_path=".env")

# Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI application
app = FastAPI()

# Storage for tasks and messages
pending_tasks = {}
pending_messages = {}


# --- Telegram Handlers ---
@dp.message()
async def handle_user_message(message: types.Message):
    chat_id = message.chat.id

    # Check if there is a pending task for this chat
    if chat_id in pending_tasks:
        # Check if the user is replying to the bot's message
        if (
            message.reply_to_message
            and message.reply_to_message.message_id == pending_messages[chat_id]
        ):
            task = pending_tasks.pop(chat_id)  # Remove task from queue
            pending_messages.pop(chat_id, None)  # Remove message from queue
            task.set_result(message.text)  # Return result to task
            await message.reply("Thank you! Release notes accepted.")
        else:
            await message.reply("Please use the 'Reply' function on the bot's message.")
    else:
        await message.reply("No active translation request. Try again later.")


def translate_text(text: str, target_language="en"):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_language.upper(),
    }
    response = requests.post(url, data=params)
    
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        raise Exception(f"Error in translation: {response.text}")


class Notes(BaseModel):
    notes: str
    chat_id: int = None
    target_language: str

# --- FastAPI Route ---
@app.post("/release_notes")
async def release_notes(data: Notes):
    try:
        translated_notes = translate_text(data.notes, target_language=data.target_language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in translation: {str(e)}")
    
    # Send message to Telegram and wait for response
    chat_id = data.chat_id or int(TELEGRAM_CHAT_ID)

    # Create asyncio.Future to wait for response
    loop = asyncio.get_event_loop()
    task = loop.create_future()
    pending_tasks[chat_id] = task

    try:
        # Send message to Telegram
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=f"New release notes for translation:\n\n<pre>{data.notes}</pre>\n\n"
                f"Translated release notes:\n\n<pre>{translated_notes}</pre>\n\n"
                "Please send the edited version using the 'Reply' function on this message.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest as e:
        if "message is too long" in str(e):
            # If message is too long, send it as a file
            file_content = (f"New release notes for translation:\n\n{data.notes}\n\n"
                            f"Translated release notes:\n\n{translated_notes}\n\n"
                            "Please send the edited version using the 'Reply' function on this message.")
            file = BytesIO(file_content.encode('utf-8'))
            file.name = "release_notes.txt"
            sent_message = await bot.send_document(
                chat_id=chat_id,
                document=file,
                caption="Release notes for translation",
            )
        else:
            raise e

    # Save bot message ID
    pending_messages[chat_id] = sent_message.message_id

    # Wait for user response
    try:
        translated_notes = await asyncio.wait_for(
            task, timeout=int(os.getenv("TRANSLATION_TIMEOUT", 600))
        )  # Timeout 10 minutes
        return {"translated_notes": translated_notes}
    except asyncio.TimeoutError as e:
        # If user did not respond within the timeout
        pending_tasks.pop(chat_id, None)  # Remove task if not completed
        pending_messages.pop(chat_id, None)
        raise HTTPException(
            status_code=408, detail="User did not respond in time"
        ) from e


# Start Aiogram
@app.on_event("startup")
async def on_startup():
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    asyncio.create_task(dp.start_polling(bot, handle_signals=False))


# Start FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
