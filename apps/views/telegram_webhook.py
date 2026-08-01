import json

from aiogram.types import Update
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.management.commands.run_bot import bot, dp


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if bot is None:
        # TELEGRAM_BOT_TOKEN sozlanmagan yoki bot yaratilmagan —
        # webhookni sekin/xato bilan javob qaytarib, Telegram tomonidan
        # qayta-qayta chaqirilishining oldini olamiz.
        return JsonResponse({"error": "bot not configured"}, status=503)

    try:
        data = json.loads(request.body.decode("utf-8"))
        update = Update(**data)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return JsonResponse({"error": "invalid payload"}, status=400)

    # Asinxron funksiyani sinxron muhitda chaqirish
    async_to_sync(dp.feed_update)(bot, update)
    return HttpResponse("ok", status=200)