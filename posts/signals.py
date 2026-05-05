from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import FamilyPost
from .newspaper_service import regenerate_quarter_for_post


@receiver(post_save, sender=FamilyPost)
def regenerate_quarterly_newspaper_on_save(sender, instance, **kwargs):
    regenerate_quarter_for_post(instance)


@receiver(post_delete, sender=FamilyPost)
def regenerate_quarterly_newspaper_on_delete(sender, instance, **kwargs):
    regenerate_quarter_for_post(instance)
