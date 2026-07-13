import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

app = Celery("root")

# settings.py dagi CELERY_ bilan boshlanuvchi barcha sozlamalarni oladi
# (jumladan CELERY_BEAT_SCHEDULE)
app.config_from_object("django.conf:settings", namespace="CELERY")

# har bir INSTALLED_APPS ichidan tasks.py larni avtomatik topadi
app.autodiscover_tasks()