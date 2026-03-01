from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    username = 'bihong'
    password = 'qldyd2#Fam'

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        },
    )

    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.password = make_password(password)
    user.save(update_fields=['is_staff', 'is_superuser', 'is_active', 'password'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_familypostvideo'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, noop_reverse),
    ]
