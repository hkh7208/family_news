import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse


logger = logging.getLogger(__name__)


def _build_post_url(post, request=None):
    post_path = reverse('post_detail', kwargs={'pk': post.pk})
    if request:
        return request.build_absolute_uri(post_path)

    site_base_url = (getattr(settings, 'SITE_BASE_URL', '') or '').rstrip('/')
    if site_base_url:
        return urljoin(f'{site_base_url}/', post_path.lstrip('/'))
    return post_path


def _build_main_image_url(post, request=None):
    if not getattr(post, 'main_image', None):
        return ''
    try:
        image_url = post.main_image.url
    except Exception:
        return ''

    if request:
        return request.build_absolute_uri(image_url)

    site_base_url = (getattr(settings, 'SITE_BASE_URL', '') or '').rstrip('/')
    if site_base_url and image_url.startswith('/'):
        return urljoin(f'{site_base_url}/', image_url.lstrip('/'))
    return image_url


def send_signup_request_notification(user):
    notify_email = (getattr(settings, 'SIGNUP_REQUEST_NOTIFY_EMAIL', '') or '').strip()
    if not notify_email:
        return False

    display_name = (user.first_name or '').strip() or '-'
    applicant_email = (user.email or '').strip() or '-'

    subject = '[가족신문] 새 회원가입 신청 알림'
    text_body = (
        '새로운 회원가입 신청이 접수되었습니다.\n\n'
        f'- 아이디: {user.username}\n'
        f'- 이름: {display_name}\n'
        f'- 이메일: {applicant_email}\n'
    )
    html_body = f"""
<h2>새로운 회원가입 신청이 접수되었습니다.</h2>
<ul>
  <li><strong>아이디</strong>: {user.username}</li>
  <li><strong>이름</strong>: {display_name}</li>
  <li><strong>이메일</strong>: {applicant_email}</li>
</ul>
""".strip()

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notify_email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Failed to send signup request notification email.')
        return False


def send_new_post_notification(post, request=None):
    recipient_emails = list(
        User.objects.filter(is_active=True)
        .exclude(email__isnull=True)
        .exclude(email__exact='')
        .exclude(pk=getattr(post, 'author_id', None))
        .values_list('email', flat=True)
        .distinct()
    )
    if not recipient_emails:
        return 0

    post_url = _build_post_url(post, request=request)
    image_url = _build_main_image_url(post, request=request)

    subject = f'[가족신문] 새 기사 등록: {post.title}'
    text_body = (
        f'새 기사가 등록되었습니다.\n\n'
        f'제목: {post.title}\n'
        f'작성자: {post.author.username}\n\n'
        f'{post.content}\n\n'
        f'기사 보기: {post_url}\n'
    )

    image_html = f'<p><img src="{image_url}" alt="기사 대표사진" style="max-width: 640px; width: 100%; height: auto;" /></p>' if image_url else ''
    html_body = f"""
<h2>새 기사가 등록되었습니다.</h2>
<p><strong>제목:</strong> {post.title}</p>
<p><strong>작성자:</strong> {post.author.username}</p>
{image_html}
<p style="white-space: pre-line;">{post.content}</p>
<p><a href="{post_url}">기사 보러 가기</a></p>
""".strip()

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[],
            bcc=recipient_emails,
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return len(recipient_emails)
    except Exception:
        logger.exception('Failed to send new post notification email. post_id=%s', post.pk)
        return 0
