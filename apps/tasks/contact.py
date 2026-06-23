# apps/tasks/contact.py
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.models import ContactMessage


@shared_task
def delete_old_contact_messages():
    threshold = timezone.now() - timedelta(days=30)
    deleted_count, _ = ContactMessage.objects.filter(created_at__lt=threshold).delete()
    return f"Deleted {deleted_count} old contact messages"
