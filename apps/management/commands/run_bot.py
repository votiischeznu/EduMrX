import asyncio
import hashlib
import json
import logging
import random

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# --- Global obyektlar: xatolik bo'lsa ham import qulamasligi kerak ---
# Redis ulanmasa yoki REDIS_URL noto'g'ri bo'lsa, butun Django (va shu bilan
# birga apps.urls orqali import qilinadigan barcha API) qulab tushmasligi kerak.
try:
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    storage = RedisStorage(redis=redis_client)
    BOT_READY = True
except Exception:
    logger.exception(
        "Redis ulanmadi (REDIS_URL='%s'). Bot MemoryStorage bilan ishga tushdi — "
        "bu faqat vaqtinchalik holat, production uchun mos emas.",
        getattr(settings, "REDIS_URL", None),
    )
    redis_client = None
    storage = MemoryStorage()
    BOT_READY = False

dp = Dispatcher(storage=storage)

try:
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
except Exception:
    logger.exception("Bot obyekti yaratilmadi — TELEGRAM_BOT_TOKEN sozlamasini tekshiring.")
    bot = None


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def _redis_required(func):
    """Redis ishlamasa, handler ichiga kirmasdan foydalanuvchiga xabar beradi."""

    async def wrapper(message: types.Message, *args, **kwargs):
        if not BOT_READY or redis_client is None:
            await message.answer("Bot vaqtincha ishlamayapti. Birozdan so'ng urinib ko'ring.")
            return
        return await func(message, *args, **kwargs)

    return wrapper


@dp.message(Command("start"))
@_redis_required
async def command_start_handler(message: types.Message, command: CommandObject):
    link_token = command.args
    if not link_token:
        await message.answer(
            "Xush kelibsiz! Ro'yxatdan o'tish, parolni tiklash yoki bildirishnomalarni ulash uchun saytdan foydalaning."
        )
        return

    raw_data = await redis_client.get(f"bot_token:{link_token}")
    if not raw_data:
        await message.answer("Xatolik: Havola muddati tugagan yoki noto'g'ri. Saytdan qayta urinib ko'ring.")
        return

    # ── 1. Profilni alohida bog'lash (email orqali ro'yxatdan o'tganlar uchun) ──
    if link_token.startswith("tglink_"):
        await _handle_profile_link(message, link_token)
        return

    data = json.loads(raw_data)

    # ── 2. Parolni tiklash (recovery) ────────────────────────────────────
    if link_token.startswith("rec_"):
        await _handle_recovery_start(message, link_token, data)
        return

    # ── 3. Ro'yxatdan o'tish (registration) — OTP + telegram_id bog'lash ──
    if link_token.startswith("reg_"):
        await _handle_registration_start(message, link_token, data)
        return

    await message.answer("Noto'g'ri havola turi.")


async def _handle_profile_link(message: types.Message, link_token: str):
    """
    Profildan 'Telegramga ulash' tugmasi bosilganda ishlaydigan oqim.
    Faqat email orqali ro'yxatdan o'tgan (hali telegram_id'si yo'q)
    foydalanuvchilar uchun kerak.
    """
    from asgiref.sync import sync_to_async

    from apps.models import User

    user_id = await redis_client.get(f"bot_token:{link_token}")
    if not user_id:
        await message.answer("Havola muddati tugagan. Saytdan qayta urinib ko'ring.")
        return

    chat_id = message.from_user.id
    username = message.from_user.username or ""

    @sync_to_async
    def _link():
        already_taken = User.objects.filter(telegram_id=chat_id).exclude(id=user_id).exists()
        if already_taken:
            return "taken"

        user = User.objects.filter(id=user_id).first()
        if not user:
            return "not_found"

        user.telegram_id = chat_id
        user.telegram_username = username
        user.telegram_linked_at = timezone.now()
        user.save(update_fields=["telegram_id", "telegram_username", "telegram_linked_at"])
        return "ok"

    result = await _link()

    if result == "taken":
        await message.answer("Bu Telegram akkaunt allaqachon boshqa foydalanuvchiga bog'langan.")
    elif result == "not_found":
        await message.answer("Foydalanuvchi topilmadi. Saytdan qayta urinib ko'ring.")
    else:
        await redis_client.delete(f"bot_token:{link_token}")
        await message.answer(
            "✅ Hisobingiz muvaffaqiyatli ulandi!\n\nEndi tizimdagi muhim bildirishnomalar shu botga keladi."
        )


async def _handle_recovery_start(message: types.Message, link_token: str, data: dict):
    user_id = data["user_id"]

    existing = await redis_client.get(f"otp_verification:{user_id}")
    if existing:
        await message.answer(
            "Sizga tasdiqlash kodi allaqachon yuborilgan. Iltimos, o'sha koddan foydalaning yoki biroz kuting."
        )
        return

    otp_code = str(random.randint(100000, 999999))
    payload = {
        "otp": hash_otp(otp_code),
        "new_phone": data["new_phone"],
        "method": "telegram_bot",
        "verified": False,
        "attempts": 0,
    }

    await redis_client.setex(f"otp_verification:{user_id}", 300, json.dumps(payload))

    await message.answer(
        f"Parolni tiklash tasdiqlandi ✅\n\nTasdiqlash kodi: <b>{otp_code}</b>\n\nUshbu kodni saytga kiriting."
    )
    await redis_client.delete(f"bot_token:{link_token}")


async def _handle_registration_start(message: types.Message, link_token: str, data: dict):
    """
    Registratsiya paytida method=telegram_bot tanlangan bo'lsa,
    foydalanuvchi shu yerda /start bosadi.

    Bu yerda IKKI ish bajariladi:
    1. OTP kod generatsiya qilinadi va ko'rsatiladi (avvalgidek).
    2. chat_id Redisga vaqtincha saqlanadi (otp_verification ichida),
       chunki user hali User jadvalida yaratilmagan — yaratilish
       complete_registration bosqichida bo'ladi. Shu sababli telegram_id
       OTPService.complete_registration ichida User.objects.create_user
       chaqirilganda birga saqlanadi (services.py'da ko'rsatiladi).
    """
    phone = data["phone"]

    existing_raw = await redis_client.get(f"otp_verification:{phone}")
    if not existing_raw:
        await message.answer(
            "Ro'yxatdan o'tish seansi topilmadi yoki muddati tugagan. Saytdan qayta ro'yxatdan o'ting."
        )
        return

    existing_data = json.loads(existing_raw)
    otp_code = str(random.randint(1000, 9999))

    existing_data["otp"] = hash_otp(otp_code)
    existing_data["attempts"] = 0
    # Telegram orqali kelgan chat_id va username'ni saqlaymiz —
    # registratsiya yakunlanganda User.telegram_id sifatida yoziladi.
    existing_data["telegram_chat_id"] = message.from_user.id
    existing_data["telegram_username"] = message.from_user.username or ""

    await redis_client.setex(f"otp_verification:{phone}", 300, json.dumps(existing_data))

    await message.answer(
        "Ro'yxatdan o'tish jarayoni boshlandi! 🎉\n\n"
        f"Sizning tasdiqlash kodingiz: <b>{otp_code}</b>\n\n"
        "Ushbu kodni saytga kiritib, ro'yxatdan o'tishni yakunlang.\n\n"
        "✅ Hisobingiz ro'yxatdan o'tgach, shu Telegram akkaunt avtomatik "
        "ulangan bo'ladi — bildirishnomalar shu yerga keladi."
    )
    await redis_client.delete(f"bot_token:{link_token}")


class Command(BaseCommand):
    help = "Bot webhook'ini o'rnatish"

    def handle(self, *args, **options):
        if bot is None:
            self.stderr.write(self.style.ERROR("Bot obyekti yaratilmagan — TELEGRAM_BOT_TOKEN ni tekshiring."))
            return

        webhook_url = f"{settings.WEBHOOK_URL}/webhook/bot/"
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.set_webhook(webhook_url))
        self.stdout.write(self.style.SUCCESS(f"Webhook {webhook_url} ga o'rnatildi."))