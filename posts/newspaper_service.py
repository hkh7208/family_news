from datetime import date
from io import BytesIO
from textwrap import shorten

from django.core.files.base import ContentFile
from django.db import transaction

from .models import FamilyPost, QuarterlyNewspaper

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    REPORTLAB_READY = True
except ImportError:
    REPORTLAB_READY = False


def _quarter_from_month(month):
    return ((month - 1) // 3) + 1


def get_year_quarter(value):
    value_date = value.date() if hasattr(value, 'date') else value
    return value_date.year, _quarter_from_month(value_date.month)


def quarter_date_range(year, quarter):
    start_month = (quarter - 1) * 3 + 1
    start_date = date(year, start_month, 1)
    if quarter == 4:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, start_month + 3, 1)
    return start_date, end_date


def _quarter_label(year, quarter):
    short_year = str(year)[-2:]
    return f'{short_year}년 {quarter}분기 가족신문'


def _build_issue_pdf(posts, year, quarter):
    if not REPORTLAB_READY:
        return None

    buffer = BytesIO()
    page_width, page_height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)

    body_font = 'Helvetica'
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HYGothic-Medium'))
        body_font = 'HYGothic-Medium'
    except Exception:
        pass

    issue_title = _quarter_label(year, quarter)
    y = page_height - 56

    pdf.setFont(body_font, 24)
    pdf.drawString(38, y, issue_title)
    y -= 24
    pdf.setFont(body_font, 11)
    pdf.drawString(38, y, f'기사 수: {len(posts)}')
    y -= 18
    pdf.setLineWidth(1)
    pdf.line(38, y, page_width - 38, y)
    y -= 20

    for idx, post in enumerate(posts, start=1):
        if y < 130:
            pdf.showPage()
            y = page_height - 48
            pdf.setFont(body_font, 14)
            pdf.drawString(38, y, issue_title)
            y -= 24

        pdf.setFont(body_font, 13)
        pdf.drawString(38, y, f'{idx}. {shorten(post.title, width=46, placeholder="...")}')
        y -= 15

        meta_text = f'{post.created_at:%Y-%m-%d} | {post.author.username}'
        pdf.setFont(body_font, 9)
        pdf.drawString(38, y, meta_text)
        y -= 10

        summary = shorten((post.content or '').replace('\n', ' '), width=180, placeholder='...')
        pdf.setFont(body_font, 10)
        pdf.drawString(38, y, summary)
        y -= 16

        if post.main_image:
            try:
                image_reader = ImageReader(post.main_image.path)
                pdf.drawImage(image_reader, 38, y - 120, width=170, height=110, preserveAspectRatio=True, anchor='sw')
                y -= 124
            except Exception:
                y -= 8

        pdf.setLineWidth(0.5)
        pdf.line(38, y, page_width - 38, y)
        y -= 16

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_quarterly_newspaper(year, quarter):
    start_date, end_date = quarter_date_range(year, quarter)
    quarter_posts = list(
        FamilyPost.objects.select_related('author')
        .filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
        .order_by('created_at')
    )

    existing_issue = QuarterlyNewspaper.objects.filter(year=year, quarter=quarter).first()
    if not quarter_posts:
        if existing_issue:
            existing_issue.delete()
        return None

    pdf_bytes = _build_issue_pdf(quarter_posts, year, quarter)
    if not pdf_bytes:
        return None

    issue_title = _quarter_label(year, quarter)
    issue, _ = QuarterlyNewspaper.objects.get_or_create(
        year=year,
        quarter=quarter,
        defaults={
            'title': issue_title,
            'article_count': len(quarter_posts),
        },
    )
    issue.title = issue_title
    issue.article_count = len(quarter_posts)

    file_name = f'family_news_{year}_q{quarter}.pdf'
    if issue.pdf_file:
        issue.pdf_file.delete(save=False)
    issue.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
    issue.save()
    return issue


def sync_all_quarterly_newspapers():
    if not REPORTLAB_READY:
        return []

    quarter_keys = {
        get_year_quarter(created_at)
        for created_at in FamilyPost.objects.values_list('created_at', flat=True)
    }
    generated = []
    for year, quarter in sorted(quarter_keys, reverse=True):
        issue = generate_quarterly_newspaper(year, quarter)
        if issue:
            generated.append(issue)

    QuarterlyNewspaper.objects.exclude(
        year__in=[year for year, _ in quarter_keys],
    ).delete()

    existing_pairs = {(year, quarter) for year, quarter in quarter_keys}
    for stale_issue in QuarterlyNewspaper.objects.all():
        if (stale_issue.year, stale_issue.quarter) not in existing_pairs:
            stale_issue.delete()

    return generated


def regenerate_quarter_for_post(post):
    if not REPORTLAB_READY or not post:
        return

    year, quarter = get_year_quarter(post.created_at)
    transaction.on_commit(lambda: generate_quarterly_newspaper(year, quarter))
