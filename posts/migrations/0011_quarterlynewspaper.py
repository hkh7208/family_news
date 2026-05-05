from django.db import migrations, models
import posts.models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_familypostcomment_emoji'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuarterlyNewspaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField(verbose_name='연도')),
                ('quarter', models.PositiveSmallIntegerField(verbose_name='분기')),
                ('title', models.CharField(max_length=120, verbose_name='신문 제목')),
                ('article_count', models.PositiveIntegerField(default=0, verbose_name='기사 수')),
                ('pdf_file', models.FileField(upload_to=posts.models.quarterly_pdf_upload_to, verbose_name='신문 PDF')),
                ('generated_at', models.DateTimeField(auto_now=True, verbose_name='생성일')),
            ],
            options={
                'verbose_name': '분기 신문',
                'verbose_name_plural': '분기 신문',
                'ordering': ['-year', '-quarter'],
                'unique_together': {('year', 'quarter')},
            },
        ),
    ]
