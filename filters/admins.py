from data.config import ADMINS
from aiogram.dispatcher.filters.filters import Filter
from aiogram import types

class IsAdmin(Filter):
    async def check(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS
