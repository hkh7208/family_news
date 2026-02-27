from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_familypostimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='familypost',
            name='event_date',
            field=models.DateField(blank=True, null=True, verbose_name='이벤트 날짜'),
        ),
    ]
