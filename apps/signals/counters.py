from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from apps.models.centers import Center
from apps.models.profiles import Student
from apps.models.groups import Group

@receiver(post_save, sender=Student)
def update_center_total_students_on_save(sender, instance, created, **kwargs):
    if created and instance.center_id:
        Center.objects.filter(id=instance.center_id).update(total_students=F("total_students") + 1)

@receiver(post_delete, sender=Student)
def update_center_total_students_on_delete(sender, instance, **kwargs):
    if instance.center_id:
        Center.objects.filter(id=instance.center_id).update(total_students=F("total_students") - 1)

@receiver(post_save, sender=Group)
def update_center_total_groups_on_save(sender, instance, created, **kwargs):
    if created and instance.center_id:
        Center.objects.filter(id=instance.center_id).update(total_groups=F("total_groups") + 1)

@receiver(post_delete, sender=Group)
def update_center_total_groups_on_delete(sender, instance, **kwargs):
    if instance.center_id:
        Center.objects.filter(id=instance.center_id).update(total_groups=F("total_groups") - 1)
