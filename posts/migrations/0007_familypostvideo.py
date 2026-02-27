from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_familypost_event_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='FamilyPostVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', models.FileField(upload_to='family_posts/videos/%Y/%m/%d/', verbose_name='동영상')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='등록일')),
                ('post', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='videos', to='posts.familypost', verbose_name='기사')),
            ],
            options={
                'verbose_name': '기사 동영상',
                'verbose_name_plural': '기사 동영상',
                'ordering': ['created_at'],
            },
        ),
    ]
