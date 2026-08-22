import asyncio
import json
import logging

from aiogram.types import Update
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.management.commands.run_bot import bot, bot_loop, dp

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if bot is None:
        return JsonResponse({"error": "bot not configured"}, status=503)
    try:
        data = json.loads(request.body.decode("utf-8"))
        update = Update(**data)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return JsonResponse({"error": "invalid payload"}, status=400)

    future = asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), bot_loop)
    try:
        future.result(timeout=15)
    except Exception:
        logger.exception("feed_update xato berdi")
    return HttpResponse("ok", status=200)
