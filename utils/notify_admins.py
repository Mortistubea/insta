import logging


from aiogram import Dispatcher

from data.config import ADMINS



async def on_startup_notify(dp):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, "Bot has started!")

        except Exception as err:
            logging.basicConfig(level=logging.INFO)