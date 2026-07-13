import json

from aiogram.types import Update
from asgiref.sync import async_to_sync  # Bu kutubxonani qo'shing
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Importlarni 'run_bot' faylidan emas, balki botni alohida konfiguratsiya qiladigan fayldan oling
from apps.management.commands.run_bot import bot, dp


@csrf_exempt
def telegram_webhook(request):  # 'async' ni olib tashladik
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        update = Update(**data)

        # Asinxron funksiyani sinxron muhitda chaqirish
        async_to_sync(dp.feed_update)(bot, update)

        return HttpResponse("ok", status=200)

    return JsonResponse({"error": "Method not allowed"}, status=405)
