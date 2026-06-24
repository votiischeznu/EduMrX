# apps/views/telegram_link.py
"""
Email orqali ro'yxatdan o'tgan (hali telegram_id'si bo'lmagan)
foydalanuvchilar profilidan "Telegramga ulash" tugmasini bosganda
ishlaydigan view'lar.

Telegram orqali ro'yxatdan o'tganlar uchun bu shart emas — ularning
telegram_id'si registratsiya paytida avtomatik saqlangan
(redis_otp.py -> OTPService.complete_registration).
"""
import uuid

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.service.redis_otp import r
from apps.service.telegram_bot import TelegramBotService

LINK_TTL = 600
LINK_PREFIX = "tglink_"


def _link_key(token: str) -> str:
    return f"bot_token:{LINK_PREFIX}{token}"


@extend_schema(tags=["Telegram"])
class TelegramLinkStartView(APIView):
    """Foydalanuvchi uchun bot bilan bog'lanish havolasini generatsiya qiladi."""
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user

        if user.telegram_id:
            return Response(
                {
                    "message": "Sizning hisobingiz allaqachon Telegramga ulangan.",
                    "already_linked": True,
                    "telegram_username": user.telegram_username,
                }
            )

        token = uuid.uuid4().hex[:16]
        r.setex(_link_key(token), LINK_TTL, str(user.id))

        bot_username = TelegramBotService.get_bot_username()

        return Response(
            {
                "message": "Quyidagi havola orqali botga o'ting va START tugmasini bosing.",
                "bot_link": f"https://t.me/{bot_username}?start={LINK_PREFIX}{token}",
                "already_linked": False,
                "expires_in": LINK_TTL,
            }
        )


@extend_schema(tags=["Telegram"])
class TelegramLinkStatusView(APIView):
    """Frontend bu endpoint orqali bog'lanish holatini tekshiradi (polling)."""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        return Response(
            {
                "linked": bool(user.telegram_id),
                "telegram_username": user.telegram_username or "",
                "linked_at": user.telegram_linked_at,
            }
        )