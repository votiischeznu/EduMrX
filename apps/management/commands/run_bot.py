import asyncio
import json
import logging
import sys
import hashlib
import random
from django.core.management.base import BaseCommand
from django.conf import settings

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
storage = RedisStorage(redis=redis_client)
dp = Dispatcher(storage=storage)

logger = logging.getLogger(__name__)


def hash_otp(otp: str):
    return hashlib.sha256(otp.encode()).hexdigest()


@dp.message(Command("start"))
async def command_start_handler(message: types.Message, command: CommandObject):
    link_token = command.args
    if not link_token:
        await message.answer("Xush kelibsiz! Tizimga kirish yoki parolni tiklash uchun saytdan foydalaning.")
        return

    raw_data = await redis_client.get(f"bot_token:{link_token}")
    if not raw_data:
        await message.answer("Xatolik: Havola muddati tugagan yoki noto'g'ri. Saytdan qayta urinib ko'ring.")
        return

    data = json.loads(raw_data)

    if link_token.startswith("rec_"):
        user_id = data['user_id']

        existing = await redis_client.get(f"otp_verification:{user_id}")
        if existing:
            await message.answer(
                "Sizga tasdiqlash kodi allaqachon yuborilgan. Iltimos, o'sha koddan foydalaning yoki biroz kuting.")
            return

        otp_code = str(random.randint(100000, 999999))
        payload = {
            'otp': hash_otp(otp_code),
            'new_phone': data['new_phone'],
            'method': 'telegram_bot',
            'verified': False,
            'attempts': 0
        }

        await redis_client.setex(f"otp_verification:{user_id}", 300, json.dumps(payload))

        await message.answer((
            "Parolni tiklash tasdiqlandi ✅\n\n"
            f"Tasdiqlash kodi: <b>{otp_code}</b>\n\n"
            "Ushbu kodni saytga kiriting."
        ))

        await redis_client.delete(f"bot_token:{link_token}")
    else:
        await message.answer("Noto'g'ri havola turi.")


class Command(BaseCommand):
    help = "Aiogram Telegram Botini Django ichida ishga tushirish"

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            stream=sys.stdout
        )
        self.stdout.write(self.style.SUCCESS("Telegram bot poller Django muhitida ishga tushmoqda..."))

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        try:
            asyncio.run(dp.start_polling(bot))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bot to'xtatildi."))