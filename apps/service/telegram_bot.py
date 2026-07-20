# apps/service/telegram_bot.py
"""
Telegramga xabar yuborish uchun yagona markaziy servis.

Aiogram polling (run_bot.py) faqat foydalanuvchidan keladigan
xabarlarni (/start) qabul qilish uchun kerak. Xabar YUBORISH uchun
aiogramga ehtiyoj yo'q — oddiy HTTP POST orqali Bot API'ga
to'g'ridan-to'g'ri murojaat qilish kifoya.
"""
import logging

import httpx
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


class TelegramBotService:
    """Telegram Bot API bilan sinxron ishlash uchun yagona nuqta."""

    @staticmethod
    def _get_token() -> str:
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN sozlanmagan (.env tekshiring).")
        return token

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    def _send_request(url: str, payload: dict):
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response

    @classmethod
    def send_message(cls, chat_id: int | str, text: str, parse_mode: str | None = "HTML") -> bool:
        """
        Berilgan chat_id'ga xabar yuboradi.
        Xatolik bo'lsa exception ko'tarmaydi — log yozadi va False qaytaradi,
        chunki Telegram yuborilmasligi asosiy so'rovni to'xtatib qo'ymasligi kerak.
        """
        token = cls._get_token()
        url = TELEGRAM_API_BASE.format(token=token, method="sendMessage")

        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            cls._send_request(url, payload)
            return True
        except httpx.HTTPStatusError as e:
            logger.error(
                "Telegram sendMessage xatolik: chat_id=%s status=%s body=%s",
                chat_id, e.response.status_code, e.response.text,
            )
            return False
        except (httpx.RequestError, Exception) as e:
            logger.error("Telegram sendMessage xatolik: chat_id=%s err=%s", chat_id, e)
            return False

    @classmethod
    def send_bulk(cls, chat_ids: list[int], text: str, parse_mode: str | None = "HTML") -> dict:
        """
        Bir nechta chat_id'ga ketma-ket yuboradi.
        Natija: {"sent": int, "failed": int}
        """
        sent, failed = 0, 0
        for chat_id in chat_ids:
            if cls.send_message(chat_id, text, parse_mode=parse_mode):
                sent += 1
            else:
                failed += 1
        return {"sent": sent, "failed": failed}

    @classmethod
    def get_bot_username(cls) -> str:
        return getattr(settings, "TELEGRAM_BOT_USERNAME", "edu_verify_system_bot")