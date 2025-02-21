from aiogram import types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import Message, ContentType
from aiogram.utils import executor
from instaloader import Instaloader, Post
from loader import dp,bot
import os,requests
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,CallbackQuery
import sqlite3
from data.config import ADMINS
from aiogram.types import InputFile
import aiohttp,yt_dlp,shutil
from pytube import YouTube
import pytube
import asyncio,re




@dp.message_handler(commands=["start"])
async def user_start(message: types.Message):
    await message.answer("SALOM {message.from_user.first_name}")



@dp.message_handler()
async def check_subscription_on_message(message: types.Message):
    
    # Agar foydalanuvchi barcha kanallarga obuna bo'lgan bo'lsa, keyingi bosqichni davom ettirish
    await UserStates.waiting_for_next_step.set() # Foydalanuvchi xabarini ishlov berish davom ettiriladi



    
@dp.message_handler(state=UserStates.waiting_for_next_step)
async def next_step(message: types.Message, state: FSMContext):
    link = message.text.strip()

    # Instagram havolasini tekshirish
    if "instagram.com" in link:
        await handle_instagram_download(message, link)


    elif "youtube.com" in message.text or "youtu.be" in message.text:
        await handle_youtube_download(message, message.text, state)



    # Havola noto‘g‘ri bo‘lsa
    else:
        await message.reply("Iltimos, haqiqiy Instagram yoki YouTube havolasini yuboring!")


async def handle_instagram_download(message: types.Message, link: str):
    try:
        response = requests.get(
            "https://instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com/get-info-rapidapi",
            headers={
                "x-rapidapi-key": "e0d0b80011msh54bf0d1a19c1620p1c0c19jsn1d6878714453",
                "x-rapidapi-host": "instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com"
            },
            params={"url": link}
        ).json()

        if response.get("error"):
            await message.reply("Xato yuz berdi yoki media topilmadi. Iltimos, qayta urinib ko'ring.")
            return

        media_type = response.get("type")
        if media_type == "album":
            medias = response.get("medias", [])
            for media in medias:
                if media["type"] == "image":
                    await bot.send_photo(message.chat.id, media["download_url"])
                elif media["type"] == "video":
                    await bot.send_video(message.chat.id, media["download_url"])
        elif media_type == "video":
            await bot.send_video(message.chat.id, response["download_url"])
        elif media_type == "image":
            await bot.send_photo(message.chat.id, response["download_url"])
        else:
            await message.reply("Media topilmadi. Havolani tekshiring yoki boshqa media yuboring.")
    except Exception as e:
        print(f"Xatolik: {e}")
        await message.reply("Xatolik yuz berdi! Qaytadan urinib ko'ring.")




async def handle_youtube_download(message: Message, link: str, state: FSMContext):
    if state is None:
        await message.reply("❌ Xatolik: Holat mavjud emas.")
        return

    await state.update_data(url=link)  # Havolani saqlash
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎥 Video", callback_data="youtube_video"),
        InlineKeyboardButton("🎵 Audio", callback_data="youtube_audio")
    )
    
    await message.reply("📥 Yuklab olish turini tanlang:", reply_markup=keyboard)
    await UserStates.waiting_for_type.set()

@dp.callback_query_handler(lambda call: call.data in ["youtube_video", "youtube_audio"], state=UserStates.waiting_for_type)
async def choose_download_type(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data.get("url")
    
    if call.data == "youtube_video":
        await call.message.answer("⏳ Video yuklab olinmoqda, biroz kuting...")
        filename = await download_youtube_video(url)
        if filename:
            with open(filename, "rb") as video:
                await bot.send_video(call.message.chat.id, video)
            os.remove(filename)
        else:
            await call.message.answer("❌ Xatolik yuz berdi.")
    else:
        await call.message.answer("⏳ MP3 formatida yuklab olinmoqda, biroz kuting...")
        filename = await download_youtube_audio(url)
        if filename:
            with open(filename, "rb") as audio:
                await bot.send_audio(call.message.chat.id, audio)
            os.remove(filename)
        else:
            await call.message.answer("❌ Xatolik yuz berdi.")
    await state.finish()

async def download_youtube_video(link: str):
    ydl_opts = {
        "format": "best[ext=mp4]",
        "outtmpl": "downloads/%(title)s.%(ext)s"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        return filename
    except Exception:
        return None

async def download_youtube_audio(link: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ]
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
        return filename
    except Exception:
        return None
