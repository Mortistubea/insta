from aiogram import types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import Message
from loader import dp, bot
from data.config import ADMINS
import sqlite3,requests
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove
from filters.admins import IsAdmin

# Ma'lumotlar bazasi bilan ishlash uchun ulanishlar
channels_db = sqlite3.connect('channels.db')
channels_cursor = channels_db.cursor()

channels_cursor.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")

vip_db = sqlite3.connect("vip_admins.db")
vip_cursor = vip_db.cursor()

# VIP jadvalini yaratish
vip_cursor.execute("CREATE TABLE IF NOT EXISTS vip (id INTEGER PRIMARY KEY AUTOINCREMENT, vips TEXT UNIQUE)")
vip_db.commit()

class Admin(StatesGroup):
    start_admin = State()
    add_vip = State()
    add_channel = State()
    remove_channel = State()
    remove_vip = State()


@dp.message_handler(IsAdmin(), commands=['start'])
async def user_start(message: types.Message, state: FSMContext):
    # Davlatni tugatish (agar oldingi davlat tugallanmagan bo'lsa)
    await state.finish()

    # Reply keyboardni yaratish
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("➕ Kanal qo'shish"),
        KeyboardButton("➖ Kanalni o'chirish"),
        KeyboardButton("📋 Barcha kanallar"),
        KeyboardButton("⭐ VIP foydalanuvchi qo'shish"),
        KeyboardButton("❌ VIP foydalanuvchini o'chirish"),
    ]
    keyboard.add(*buttons)

    await message.reply(
        "Admin paneliga xush kelibsiz! Quyidagilardan birini tanlang:",
        reply_markup=keyboard
    )



@dp.message_handler(IsAdmin(), lambda message: message.text == "➕ Kanal qo'shish")
async def save_channel(message: types.Message, state: FSMContext):
    await state.finish()  # Eski holatlarni tugatish
    await message.reply("Kanal username'ni '@' bilan yuboring:", reply_markup=ReplyKeyboardRemove())
    await Admin.add_channel.set()


@dp.message_handler(IsAdmin(),lambda message: message.text == "➖ Kanalni o'chirish")
async def remove_channel_start(message: types.Message):
    await message.reply("O'chirish uchun kanal username'ni kiriting:")
    await Admin.remove_channel.set()

@dp.message_handler(IsAdmin(), lambda message: message.text == "📋 Barcha kanallar")
async def all_channels_handler(message: types.Message):
    channels_cursor.execute("SELECT id, name FROM channels")
    channels = channels_cursor.fetchall()

    if not channels:
        await message.reply("📋 Hech qanday kanal topilmadi.")
        return

    channel_list = "📋 <b>Barcha kanallar:</b>\n\n"
    for channel_id, channel_name in channels:
        channel_list += f"🆔 ID: <code>{channel_id}</code>\n📢 Kanal: {channel_name}\n\n"

    await message.reply(channel_list, parse_mode=types.ParseMode.HTML)


@dp.message_handler(IsAdmin(), lambda message: message.text == "⭐ VIP foydalanuvchi qo'shish")
async def add_vip_process(message: types.Message, state: FSMContext):
    # Davlatni tugatish (oldingi holatlarni tozalash uchun)
    await state.finish()

    await message.reply("VIP foydalanuvchini username'ni '@' bilan yuboring:", reply_markup=ReplyKeyboardRemove())
    await Admin.add_vip.set()


@dp.message_handler(state=Admin.add_vip)
async def save_vip_user(message: types.Message, state: FSMContext):
    vip_username = message.text.strip()

    # Username to'g'riligini tekshirish
    if not vip_username.startswith("@"):
        await message.reply("Foydalanuvchi username '@' bilan boshlanishi kerak. Iltimos, qaytadan kiriting:")
        return

    try:
        # VIP foydalanuvchini bazaga qo'shish
        vip_cursor.execute("INSERT OR IGNORE INTO vip (vips) VALUES (?)", (vip_username,))
        vip_db.commit()
        await message.reply(f"🌟 VIP foydalanuvchi muvaffaqiyatli qo'shildi: {vip_username}")
    except sqlite3.IntegrityError:
        await message.reply("❌ Bu foydalanuvchi allaqachon VIP sifatida mavjud.")
    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {e}")
    finally:
        # Holatni yakunlash
        await state.finish()

@dp.message_handler(IsAdmin(), lambda message: message.text == "❌ VIP foydalanuvchini o'chirish")
async def remove_vip_start(message: types.Message, state: FSMContext):
    await state.finish()  # Eski holatlarni tugatish
    await message.reply("O'chirish uchun VIP foydalanuvchi username'ni kiriting:", reply_markup=ReplyKeyboardRemove())
    await Admin.remove_vip.set()


@dp.message_handler(IsAdmin(),lambda message: "instagram.com" in message.text.lower())
async def next_step(message: types.Message, state: FSMContext):


    link = message.text.strip()

    if "instagram.com" not in link:
        await message.reply("Iltimos, haqiqiy Instagram havolasini yuboring!")
        return

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
            await message.reply("Video yuklanmoqda...")
            await bot.send_video(message.chat.id, response["download_url"])
        elif media_type == "image":
            await message.reply("Rasm yuklanmoqda...")
            await bot.send_photo(message.chat.id, response["download_url"])
        else:
            await message.reply("Media topilmadi. Havolani tekshiring yoki boshqa media yuboring.")
    except Exception as e:
        print(f"Xatolik: {e}")
        await message.reply("Xatolik yuz berdi! Qaytadan urinib ko'ring.")



@dp.message_handler(state=Admin.add_channel)
async def save_channel_to_db(message: types.Message, state: FSMContext):

    channel_username = message.text.strip()

    # '@' bilan boshlanishini tekshirish
    if not channel_username.startswith("@"):
        await message.reply("❌ Kanal username '@' bilan boshlanishi kerak. Iltimos, qaytadan kiriting.")
        return

    try:
        # Kanalni ma'lumotlar bazasiga qo'shish
        channels_cursor.execute("INSERT OR IGNORE INTO channels (channel_name) VALUES (?)", (channel_username,))
        channels_db.commit()

        # Kanal muvaffaqiyatli qo'shildi
        await message.reply(f"✅ Kanal muvaffaqiyatli qo'shildi: {channel_username}")
    except sqlite3.IntegrityError:
        await message.reply("❌ Bu kanal allaqachon mavjud.")
    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {e}")
    finally:
        await state.finish()  # Davlat holatini tugatish
