# posts/models.py
from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name='태그명')

    class Meta:
        ordering = ['name']
        verbose_name = '태그'
        verbose_name_plural = '태그'

    def __str__(self):
        return self.name


class FamilyMemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='family_profile', verbose_name='사용자')
    display_name = models.CharField(max_length=50, blank=True, verbose_name='표시 이름')
    emoji = models.CharField(max_length=10, default='🙂', blank=True, verbose_name='이모티콘')
    photo = models.ImageField(upload_to='family_members/profile/%Y/%m/%d/', blank=True, null=True, verbose_name='프로필 사진')
    bio = models.CharField(max_length=200, blank=True, verbose_name='소개')

    class Meta:
        verbose_name = '가족 구성원 프로필'
        verbose_name_plural = '가족 구성원 프로필'

    def __str__(self):
        return self.display_name or self.user.get_username()


class FamilyMemberPhoto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_photos', verbose_name='사용자')
    image = models.ImageField(upload_to='family_members/photos/%Y/%m/%d/', verbose_name='사진')
    caption = models.CharField(max_length=120, blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '가족 개인 사진'
        verbose_name_plural = '가족 개인 사진'

    def __str__(self):
        return f'{self.user.username} - {self.caption or self.created_at.strftime("%Y-%m-%d")}'

class FamilyPost(models.Model):
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    # 이미지 필드: 'family_photos/' 폴더에 저장됨
    main_image = models.ImageField(upload_to='family_photos/%Y/%m/%d/', verbose_name="대표 사진")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    event_date = models.DateField(blank=True, null=True, verbose_name='이벤트 날짜')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='태그')
    
    # 매거진 스타일을 위한 '중요 포스트(히어로 이미지용)' 체크 박스
    is_hero = models.BooleanField(default=False, verbose_name="메인 히어로 설정")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class FamilyPostImage(models.Model):
    post = models.ForeignKey(FamilyPost, on_delete=models.CASCADE, related_name='images', verbose_name='기사')
    image = models.ImageField(upload_to='family_posts/multi/%Y/%m/%d/', verbose_name='추가 사진')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        ordering = ['created_at']
        verbose_name = '기사 추가 사진'
        verbose_name_plural = '기사 추가 사진'

    def __str__(self):
        return f'{self.post.title} - {self.created_at:%Y-%m-%d %H:%M}'


class FamilyPostVideo(models.Model):
    post = models.ForeignKey(FamilyPost, on_delete=models.CASCADE, related_name='videos', verbose_name='기사')
    video = models.FileField(upload_to='family_posts/videos/%Y/%m/%d/', verbose_name='동영상')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        ordering = ['created_at']
        verbose_name = '기사 동영상'
        verbose_name_plural = '기사 동영상'

    def __str__(self):
        return f'{self.post.title} - {self.created_at:%Y-%m-%d %H:%M}'


class FamilyPostComment(models.Model):
    EMOJI_CHOICES = [
        ('🙂', '🙂'),
        ('😀', '😀'),
        ('😍', '😍'),
        ('👏', '👏'),
        ('🎉', '🎉'),
        ('❤️', '❤️'),
        ('👍', '👍'),
    ]

    post = models.ForeignKey(FamilyPost, on_delete=models.CASCADE, related_name='comments', verbose_name='기사')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_post_comments', verbose_name='작성자')
    emoji = models.CharField(max_length=5, choices=EMOJI_CHOICES, default='🙂', verbose_name='이모티콘')
    content = models.TextField(max_length=1000, verbose_name='댓글 내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '기사 댓글'
        verbose_name_plural = '기사 댓글'

    def __str__(self):
        return f'{self.post.title} - {self.author.username}'