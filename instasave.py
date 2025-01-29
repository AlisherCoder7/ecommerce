import os
import asyncio
from yt_dlp import YoutubeDL
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8135702696:AAF0F2OVhQzIYscX7OPGEI4Rv3OYSsTcHq0"
bot = AsyncTeleBot(BOT_TOKEN)
temp_data = {}


async def send_format_options(url, chat_id):
    try:
        ydl_opts = {
            'cookies': './cookies.txt',
            'quiet': True,
            'listformats': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "No Title")
            thumbnail = info.get("thumbnail", None)

        temp_data[chat_id] = {"url": url, "title": title, "message_id": None}

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎥 Video", callback_data="download_video"),
            InlineKeyboardButton("🎵 MP3 Audio", callback_data="download_audio")
        )

        description = f"<b>{title}</b>\n\nYuklash uchun formatni tanlang↓:"
        if thumbnail:
            sent_message = await bot.send_photo(chat_id, photo=thumbnail, caption=description, parse_mode="HTML",
                                                reply_markup=keyboard)
        else:
            sent_message = await bot.send_message(chat_id, description, parse_mode="HTML", reply_markup=keyboard)

        temp_data[chat_id]["message_id"] = sent_message.message_id

    except Exception as e:
        await bot.send_message(chat_id, f"Xatolik yuz berdi: {e}")


async def update_status_message(chat_id, status):
    try:
        message_id = temp_data.get(chat_id, {}).get("message_id")
        if message_id:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=status, parse_mode="HTML")
    except Exception as e:
        await bot.send_message(chat_id, f"Xatolik yuz berdi: {e}")


async def download_video(chat_id):
    try:
        url = temp_data.get(chat_id, {}).get("url")
        title = temp_data.get(chat_id, {}).get("title", "video")

        if not url:
            await bot.send_message(chat_id, "Xatolik: Havola topilmadi.")
            return

        await update_status_message(chat_id, "<b>Video serverga yuklanmoqda...</b>")

        video_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': f'{title}.%(ext)s',
        }

        with YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4")

        await update_status_message(chat_id, "<b>Video Telegramga yuklanmoqda...</b>")

        with open(filename, "rb") as file:
            await bot.send_video(chat_id, file, timeout=300)

        if os.path.exists(filename):
            os.remove(filename)

            # Remove status message after upload
        message_id = temp_data.get(chat_id, {}).get("message_id")
        if message_id:
            await bot.delete_message(chat_id, message_id)

    except Exception as e:
        await bot.send_message(chat_id, f"Xatolik yuz berdi: {e}")


async def download_audio(chat_id):
    try:
        url = temp_data.get(chat_id, {}).get("url")
        title = temp_data.get(chat_id, {}).get("title", "audio")

        if not url:
            await bot.send_message(chat_id, "Xatolik: Havola topilmadi.")
            return

        await update_status_message(chat_id, "<b>Audio serverga yuklanmoqda...</b>")

        audio_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3','preferredquality': '192',
                }
            ],
            'outtmpl': f'{title}_audio.%(ext)s',
        }

        with YoutubeDL(audio_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        await update_status_message(chat_id, "<b>Audio Telegramga yuklanmoqda...</b>")

        with open(filename, "rb") as file:
            await bot.send_audio(chat_id, file)

        if os.path.exists(filename):
            os.remove(filename)

        # Remove status message after upload
        message_id = temp_data.get(chat_id, {}).get("message_id")
        if message_id:
            await bot.delete_message(chat_id, message_id)

    except Exception as e:
        await bot.send_message(chat_id, f"Xatolik yuz berdi: {e}")


@bot.message_handler(commands=["start"])
async def send_welcome(message):
    welcome_text = (
        "👋 Salom!\n\n" 
        "🚀 Ushbu bot sizga YouTubedan:\n\n" 
        "— 📹 Video,  🔉 Audio va 📑 Subtitrni istalgan sifatda yuklab beruvchi eng tezkor bot.\n\n" 
        "🔗 Yuklash uchun havolani yuboring:"
    )
    await bot.reply_to(message, welcome_text)

@bot.message_handler(commands=["dev"])
async def send_dev_info(message):
    dev_info = (
        "⚙️ <b>Bu bot Python (telebot) dasturlash tili yordamida yaratilgan</b>\n\n" 
        "🔗 Savollar va takliflar uchun: @Alisher_coder7\n"
    )
    await bot.reply_to(message, dev_info, parse_mode="HTML")


@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    url = message.text.strip()
    if "youtube.com" in url or "youtu.be" in url:
        await send_format_options(url, message.chat.id)
        await bot.delete_message(message.chat.id, message.message_id)
    else:
        await bot.reply_to(message, "To‘g‘ri YouTube havolasini yuboring.")


@bot.callback_query_handler(func=lambda call: True)
async def handle_format_selection(call):
    if call.data == "download_video":
        await bot.answer_callback_query(call.id, "Video yuklanmoqda...")
        await download_video(call.message.chat.id)
    elif call.data == "download_audio":
        await bot.answer_callback_query(call.id, "Audio yuklanmoqda...")
        await download_audio(call.message.chat.id)


asyncio.run(bot.polling(timeout=60,request_timeout=600))



