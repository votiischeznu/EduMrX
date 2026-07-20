import json

from aiogram.types import Update
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.management.commands.run_bot import bot, dp


@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        update = Update(**data)
        # Asinxron funksiyani sinxron muhitda chaqirish
        async_to_sync(dp.feed_update)(bot, update)
        return HttpResponse("ok", status=200)
    return JsonResponse({"error": "Method not allowed"}, status=405)
