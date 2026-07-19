from celery import shared_task

@shared_task
def send_telegram_bulk_message_task(chat_ids: list[int], text: str, parse_mode: str | None = "HTML"):
    from apps.service.telegram_bot import TelegramBotService
    return TelegramBotService.send_bulk(chat_ids, text, parse_mode=parse_mode)
