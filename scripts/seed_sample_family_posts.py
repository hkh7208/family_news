import os
import sys
from io import BytesIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw

from posts.models import FamilyPost


def main():
    user_model = get_user_model()
    user = user_model.objects.filter(username='bihong').first()
    if not user:
        user = user_model.objects.filter(is_superuser=True).first()
    if not user:
        raise RuntimeError('슈퍼유저가 없어 샘플 게시글을 만들 수 없습니다.')

    sample_specs = [
        ('샘플 가족 여행 스냅', '주말에 함께 다녀온 여행의 햇살 가득한 순간을 기록했어요.', (120, 185, 180), True),
        ('샘플 주말 브런치', '집에서 함께 만든 브런치와 도란도란 이야기 나눈 시간입니다.', (157, 205, 232), False),
        ('샘플 공원 산책', '가벼운 산책으로 마음이 편안해진 하루였어요.', (166, 210, 170), False),
        ('샘플 가족 영화의 밤', '팝콘과 함께 웃고 떠든 저녁 시간을 남겨요.', (196, 186, 228), False),
    ]

    for title, _, _, _ in sample_specs:
        FamilyPost.objects.filter(title=title, author=user).delete()

    created = []
    for index, (title, content, color, is_hero) in enumerate(sample_specs, start=1):
        image = Image.new('RGB', (1600, 1000), color)
        draw = ImageDraw.Draw(image)

        overlay_color = tuple(max(c - 25, 0) for c in color)
        draw.rectangle((90, 90, 1510, 910), outline=overlay_color, width=8)
        draw.rectangle((160, 160, 1440, 840), outline=(255, 255, 255), width=4)

        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=92)

        post = FamilyPost(
            title=title,
            content=content,
            author=user,
            is_hero=is_hero,
        )
        post.main_image.save(f'sample_family_{index}.jpg', ContentFile(buffer.getvalue()), save=False)
        post.save()
        created.append(post.title)

    print(f'created_count={len(created)}')
    for item in created:
        print(item)


if __name__ == '__main__':
    main()
