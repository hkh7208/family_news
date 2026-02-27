from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import OperationalError, ProgrammingError
from django.db.models import Q, Case, When, IntegerField, Value
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps, UnidentifiedImageError
from io import BytesIO
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .forms import FamilyLoginForm, FamilyMemberCreateForm, FamilyMemberPhotoForm, FamilyPostEditForm
from .models import FamilyMemberPhoto, FamilyMemberProfile, FamilyPost, FamilyPostImage, FamilyPostVideo, Tag


MAX_VIDEO_SIZE_BYTES = 200 * 1024 * 1024
MAX_IMAGE_SIZE_BYTES = 200 * 1024 * 1024
FFMPEG_EXECUTABLE = None


def _optimize_uploaded_image(uploaded_file, max_size=(1280, 1280), quality=80):
	try:
		uploaded_file.seek(0)
		image = Image.open(uploaded_file)
		image = ImageOps.exif_transpose(image)
		image.thumbnail(max_size, Image.Resampling.LANCZOS)

		if image.mode not in ('RGB', 'L'):
			image = image.convert('RGB')

		buffer = BytesIO()
		image.save(buffer, format='JPEG', quality=quality, optimize=True)
		buffer.seek(0)

		file_name = f"{Path(uploaded_file.name).stem}.jpg"
		return ContentFile(buffer.read(), name=file_name)
	except (UnidentifiedImageError, OSError, ValueError, AttributeError):
		try:
			uploaded_file.seek(0)
		except Exception:
			pass
		return uploaded_file


def _get_user_emoji(user):
	if not user or not user.is_authenticated:
		return '🙂'
	try:
		emoji = user.family_profile.emoji
		return emoji or '🙂'
	except FamilyMemberProfile.DoesNotExist:
		return '🙂'


def _compress_uploaded_video(uploaded_file, target_max_bytes=MAX_VIDEO_SIZE_BYTES):
	input_temp_path = None
	first_output_path = None
	second_output_path = None
	original_size = getattr(uploaded_file, 'size', 0) or 0
	try:
		ffmpeg_executable = _resolve_ffmpeg_executable()
		if not ffmpeg_executable:
			if original_size and original_size <= target_max_bytes:
				uploaded_file.seek(0)
				return uploaded_file, None
			return None, '동영상 압축 도구(FFmpeg)를 찾을 수 없습니다. 서버에 FFmpeg를 설치해주세요.'

		with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix or '.mp4') as input_temp:
			for chunk in uploaded_file.chunks():
				input_temp.write(chunk)
			input_temp_path = input_temp.name

		first_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
		first_output_path = first_output.name
		first_output.close()

		base_command = [
			ffmpeg_executable,
			'-y',
			'-i',
			input_temp_path,
			'-vf',
			'scale=min(1280,iw):-2',
			'-c:v',
			'libx264',
			'-preset',
			'medium',
			'-crf',
			'28',
			'-c:a',
			'aac',
			'-b:a',
			'128k',
			'-movflags',
			'+faststart',
			first_output_path,
		]
		subprocess.run(base_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		candidate_path = first_output_path
		if os.path.getsize(candidate_path) > target_max_bytes:
			second_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
			second_output_path = second_output.name
			second_output.close()

			second_command = [
				ffmpeg_executable,
				'-y',
				'-i',
				input_temp_path,
				'-vf',
				'scale=min(960,iw):-2',
				'-c:v',
				'libx264',
				'-preset',
				'medium',
				'-crf',
				'32',
				'-c:a',
				'aac',
				'-b:a',
				'96k',
				'-movflags',
				'+faststart',
				second_output_path,
			]
			subprocess.run(second_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			candidate_path = second_output_path

		candidate_size = os.path.getsize(candidate_path)
		if candidate_size > target_max_bytes:
			if original_size and original_size <= target_max_bytes:
				with open(input_temp_path, 'rb') as original_file:
					return ContentFile(original_file.read(), name=uploaded_file.name), None
			return None, '동영상 압축 후에도 200MB를 초과합니다. 더 짧은 영상이나 해상도가 낮은 파일을 올려주세요.'

		with open(candidate_path, 'rb') as compressed_file:
			file_name = f"{Path(uploaded_file.name).stem}.mp4"
			return ContentFile(compressed_file.read(), name=file_name), None
	except FileNotFoundError:
		if original_size and original_size <= target_max_bytes and input_temp_path and os.path.exists(input_temp_path):
			with open(input_temp_path, 'rb') as original_file:
				return ContentFile(original_file.read(), name=uploaded_file.name), None
		return None, '동영상 압축 도구(FFmpeg)를 찾을 수 없습니다. 서버에 FFmpeg를 설치해주세요.'
	except subprocess.CalledProcessError:
		if original_size and original_size <= target_max_bytes and input_temp_path and os.path.exists(input_temp_path):
			with open(input_temp_path, 'rb') as original_file:
				return ContentFile(original_file.read(), name=uploaded_file.name), None
		return None, '동영상 변환 중 오류가 발생했습니다. 다른 동영상으로 다시 시도해주세요.'
	except Exception:
		return None, '동영상 처리 중 알 수 없는 오류가 발생했습니다.'
	finally:
		for temp_path in [input_temp_path, first_output_path, second_output_path]:
			if temp_path and os.path.exists(temp_path):
				try:
					os.remove(temp_path)
				except OSError:
					pass


def _extract_video_thumbnail(uploaded_file):
	input_temp_path = None
	output_image_path = None
	try:
		ffmpeg_executable = _resolve_ffmpeg_executable()
		if not ffmpeg_executable:
			return _generate_video_placeholder_image(uploaded_file), None

		with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix or '.mp4') as input_temp:
			for chunk in uploaded_file.chunks():
				input_temp.write(chunk)
			input_temp_path = input_temp.name

		output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
		output_image_path = output_temp.name
		output_temp.close()

		command = [
			ffmpeg_executable,
			'-y',
			'-i',
			input_temp_path,
			'-ss',
			'00:00:01',
			'-frames:v',
			'1',
			output_image_path,
		]
		subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		with open(output_image_path, 'rb') as image_file:
			file_name = f"{Path(uploaded_file.name).stem}_thumb.jpg"
			return ContentFile(image_file.read(), name=file_name), None
	except FileNotFoundError:
		return _generate_video_placeholder_image(uploaded_file), None
	except subprocess.CalledProcessError:
		return None, '동영상 썸네일 생성에 실패했습니다. 다른 동영상으로 다시 시도해주세요.'
	except Exception:
		return None, '동영상 썸네일 생성 중 오류가 발생했습니다.'
	finally:
		for temp_path in [input_temp_path, output_image_path]:
			if temp_path and os.path.exists(temp_path):
				try:
					os.remove(temp_path)
				except OSError:
					pass


def _resolve_ffmpeg_executable():
	global FFMPEG_EXECUTABLE
	if FFMPEG_EXECUTABLE:
		return FFMPEG_EXECUTABLE

	which_path = shutil.which('ffmpeg')
	if which_path:
		FFMPEG_EXECUTABLE = which_path
		return FFMPEG_EXECUTABLE

	local_app_data = os.environ.get('LOCALAPPDATA')
	if local_app_data:
		packages_dir = Path(local_app_data) / 'Microsoft' / 'WinGet' / 'Packages'
		if packages_dir.exists():
			candidates = list(packages_dir.rglob('ffmpeg.exe'))
			if candidates:
				FFMPEG_EXECUTABLE = str(candidates[0])
				return FFMPEG_EXECUTABLE

	return None


def _generate_video_placeholder_image(uploaded_file):
	image = Image.new('RGB', (1280, 720), color=(28, 36, 48))
	buffer = BytesIO()
	image.save(buffer, format='JPEG', quality=85)
	buffer.seek(0)
	file_name = f"{Path(uploaded_file.name).stem}_thumb.jpg"
	return ContentFile(buffer.read(), name=file_name)


def _parse_tag_names(raw_text):
	if not raw_text:
		return []
	parts = []
	hashtag_parts = re.findall(r'#([^\s#,]+)', raw_text)
	parts.extend(hashtag_parts)

	non_hashtag_text = re.sub(r'#[^\s#,]+', ' ', raw_text)
	parts.extend(re.split(r'[\s,]+', non_hashtag_text))

	parts = [piece.strip().lstrip('#') for piece in parts]
	tag_names = []
	for name in parts:
		if name and name not in tag_names:
			tag_names.append(name[:30])
	return tag_names


def _sync_post_tags(post, raw_text):
	tag_names = _parse_tag_names(raw_text)
	tag_objects = []
	for name in tag_names:
		tag_obj, _ = Tag.objects.get_or_create(name=name)
		tag_objects.append(tag_obj)
	post.tags.set(tag_objects)


def _can_manage_post(user, post):
	if not user or not user.is_authenticated:
		return False
	return user == post.author or user.username == 'bihong'


def home(request):
	try:
		all_posts = FamilyPost.objects.select_related('author').order_by('-pk')
		hero_post = all_posts.first()
		posts = all_posts.exclude(pk=hero_post.pk) if hero_post else all_posts
		major_posts = all_posts[:6]
	except (OperationalError, ProgrammingError):
		hero_post = None
		posts = []
		major_posts = []

	post_items = [
		{
			'post': post,
			'emoji': _get_user_emoji(post.author),
		}
		for post in posts
	]

	major_items = [
		{
			'post': post,
			'emoji': _get_user_emoji(post.author),
		}
		for post in major_posts
	]

	context = {
		'hero_post': hero_post,
		'hero_author_emoji': _get_user_emoji(hero_post.author) if hero_post else '🙂',
		'post_items': post_items,
		'major_items': major_items,
		'current_user_emoji': _get_user_emoji(request.user),
	}
	return render(request, 'posts/index.html', context)


def news_search(request):
	query = (request.GET.get('q') or '').strip()
	search_content = request.GET.get('search_content') == 'on'
	sort = (request.GET.get('sort') or 'latest').strip()

	result_qs = FamilyPost.objects.select_related('author').prefetch_related('tags').order_by('-pk')
	if query:
		tag_query = Q(tags__name__icontains=query)
		content_query = Q(content__icontains=query)
		if search_content:
			result_qs = result_qs.filter(tag_query | content_query).distinct()
		else:
			result_qs = result_qs.filter(tag_query).distinct()

		if sort == 'relevance':
			result_qs = result_qs.annotate(
				relevance_score=(
					Case(When(tag_query, then=Value(2)), default=Value(0), output_field=IntegerField()) +
					Case(When(content_query, then=Value(1)), default=Value(0), output_field=IntegerField())
				)
			).order_by('-relevance_score', '-pk')
		else:
			result_qs = result_qs.order_by('-pk')
	else:
		result_qs = FamilyPost.objects.none()

	paginator = Paginator(result_qs, 10)
	page_obj = paginator.get_page(request.GET.get('page'))

	result_items = [
		{
			'post': post,
			'emoji': _get_user_emoji(post.author),
			'tag_count': len(post.tags.all()),
		}
		for post in page_obj.object_list
	]

	return render(
		request,
		'posts/search.html',
		{
			'query': query,
			'search_content': search_content,
			'sort': sort,
			'page_obj': page_obj,
			'result_items': result_items,
		},
	)


def post_detail(request, pk):
	post = get_object_or_404(
		FamilyPost.objects.select_related('author').prefetch_related('tags', 'images', 'videos'),
		pk=pk,
	)
	related_posts = FamilyPost.objects.none()
	slider_images = []

	if post.main_image:
		slider_images.append(post.main_image.url)

	for extra_image in post.images.all():
		slider_images.append(extra_image.image.url)

	if post.tags.exists():
		related_posts = (
			FamilyPost.objects.select_related('author')
			.prefetch_related('tags')
			.filter(tags__in=post.tags.all())
			.exclude(pk=post.pk)
			.distinct()[:8]
		)

	related_items = [
		{
			'post': related,
			'emoji': _get_user_emoji(related.author),
		}
		for related in related_posts
	]

	return render(
		request,
		'posts/detail.html',
		{
			'post': post,
			'author_emoji': _get_user_emoji(post.author),
			'slider_images': slider_images,
			'post_videos': [video_item.video.url for video_item in post.videos.all()],
			'related_items': related_items,
			'can_manage_post': _can_manage_post(request.user, post),
		},
	)


@login_required
def edit_post(request, pk):
	post = get_object_or_404(FamilyPost, pk=pk)
	if not _can_manage_post(request.user, post):
		return redirect('post_detail', pk=post.pk)

	if request.method == 'POST':
		form = FamilyPostEditForm(request.POST, request.FILES, instance=post)
		if form.is_valid():
			image_files = [
				image_file
				for image_file in request.FILES.getlist('images')
				if getattr(image_file, 'content_type', '').startswith('image/')
			]

			for image_file in image_files:
				if getattr(image_file, 'size', 0) > MAX_IMAGE_SIZE_BYTES:
					form.add_error('images', '200메가 이상의 파일은 업로드 불가합니다.')
					return render(request, 'posts/edit_post.html', {'form': form, 'post': post})

			edited_post = form.save(commit=False)
			delete_main_image = request.POST.get('delete_main_image') == 'on'
			delete_extra_image_ids = {
				int(image_id)
				for image_id in request.POST.getlist('delete_existing_images')
				if image_id.isdigit()
			}
			remaining_extra_images = list(
				edited_post.images.exclude(pk__in=delete_extra_image_ids).order_by('created_at')
			)

			uploaded_images = [_optimize_uploaded_image(file_item) for file_item in image_files]
			representative_uploaded_image = None
			extra_uploaded_images = []

			if uploaded_images:
				main_image_index_raw = request.POST.get('main_image_index', '').strip()
				if not main_image_index_raw.isdigit():
					form.add_error('images', '새로 올린 사진 중 대표사진 체크박스를 선택해주세요.')
					return render(request, 'posts/edit_post.html', {'form': form, 'post': post})

				main_image_index = int(main_image_index_raw)
				if main_image_index < 0 or main_image_index >= len(uploaded_images):
					form.add_error('images', '대표사진 선택값이 올바르지 않습니다. 다시 선택해주세요.')
					return render(request, 'posts/edit_post.html', {'form': form, 'post': post})

				representative_uploaded_image = uploaded_images[main_image_index]
				extra_uploaded_images = [
					image_item
					for idx, image_item in enumerate(uploaded_images)
					if idx != main_image_index
				]

			if representative_uploaded_image:
				edited_post.main_image = representative_uploaded_image
			elif delete_main_image:
				if remaining_extra_images:
					promoted_image = remaining_extra_images.pop(0)
					edited_post.main_image = promoted_image.image
					delete_extra_image_ids.add(promoted_image.pk)
				else:
					form.add_error('main_image', '대표 사진을 삭제하려면 새 사진을 올리거나 기존 추가 사진을 남겨주세요.')
					return render(request, 'posts/edit_post.html', {'form': form, 'post': post})

			edited_post.save()
			_sync_post_tags(edited_post, form.cleaned_data.get('tags'))

			if delete_extra_image_ids:
				edited_post.images.filter(pk__in=delete_extra_image_ids).delete()

			for uploaded_image in extra_uploaded_images:
				FamilyPostImage.objects.create(post=edited_post, image=uploaded_image)

			messages.success(request, '기사가 수정되었습니다.')
			return redirect('post_detail', pk=post.pk)
	else:
		form = FamilyPostEditForm(instance=post)

	return render(request, 'posts/edit_post.html', {'form': form, 'post': post})


@login_required
@require_POST
def delete_post(request, pk):
	post = get_object_or_404(FamilyPost, pk=pk)
	if not _can_manage_post(request.user, post):
		return redirect('post_detail', pk=post.pk)

	post.delete()
	messages.success(request, '기사가 삭제되었습니다.')
	return redirect('home')


def family_login(request):
	if request.user.is_authenticated:
		return redirect('home')

	if request.method == 'POST':
		form = FamilyLoginForm(request, data=request.POST)
		if form.is_valid():
			login(request, form.get_user())
			return redirect('home')
	else:
		form = FamilyLoginForm(request)

	return render(request, 'posts/login.html', {'form': form})


@login_required
def family_logout(request):
	logout(request)
	return redirect('home')


@login_required
def upload_photo(request):
	if request.method == 'POST':
		form = FamilyMemberPhotoForm(request.POST, request.FILES)
		if form.is_valid():
			image_files = [
				image_file
				for image_file in request.FILES.getlist('images')
				if getattr(image_file, 'content_type', '').startswith('image/')
			]

			for image_file in image_files:
				if getattr(image_file, 'size', 0) > MAX_IMAGE_SIZE_BYTES:
					messages.error(request, '200메가 이상의 파일은 업로드 불가합니다.')
					return render(request, 'posts/upload_photo.html', {'form': form})

			uploaded_images = [_optimize_uploaded_image(file_item) for file_item in image_files]

			uploaded_videos = request.FILES.getlist('videos')
			compressed_videos = []
			for video_file in uploaded_videos:
				if getattr(video_file, 'size', 0) > MAX_VIDEO_SIZE_BYTES:
					messages.error(request, '200메가 이상의 파일은 업로드 불가합니다.')
					return render(request, 'posts/upload_photo.html', {'form': form})
				compressed_video, compress_error = _compress_uploaded_video(video_file, target_max_bytes=MAX_VIDEO_SIZE_BYTES)
				if compress_error:
					messages.error(request, compress_error)
					return render(request, 'posts/upload_photo.html', {'form': form})
				compressed_videos.append(compressed_video)

			representative_image = None
			extra_images = []

			if uploaded_images:
				main_image_index_raw = request.POST.get('main_image_index', '').strip()
				if not main_image_index_raw.isdigit():
					messages.error(request, '대표사진 체크박스를 선택해주세요.')
					return render(request, 'posts/upload_photo.html', {'form': form})

				main_image_index = int(main_image_index_raw)
				if main_image_index < 0 or main_image_index >= len(uploaded_images):
					messages.error(request, '대표사진 선택값이 올바르지 않습니다. 다시 선택해주세요.')
					return render(request, 'posts/upload_photo.html', {'form': form})

				representative_image = uploaded_images[main_image_index]
				extra_images = [
					image_item
					for idx, image_item in enumerate(uploaded_images)
					if idx != main_image_index
				]
			elif uploaded_videos:
				representative_image, thumbnail_error = _extract_video_thumbnail(uploaded_videos[0])
				if thumbnail_error:
					messages.error(request, thumbnail_error)
					return render(request, 'posts/upload_photo.html', {'form': form})
			else:
				messages.error(request, '사진 또는 동영상을 한 개 이상 선택해주세요.')
				return render(request, 'posts/upload_photo.html', {'form': form})

			caption = (form.cleaned_data.get('caption') or '').strip()
			captured_at = form.cleaned_data.get('captured_at')
			event_date = form.cleaned_data.get('event_date')

			member_photo = FamilyMemberPhoto.objects.create(
				user=request.user,
				image=representative_image,
				caption=caption,
			)
			if captured_at:
				FamilyMemberPhoto.objects.filter(pk=member_photo.pk).update(created_at=captured_at)

			post_title = caption if caption else f'{request.user.username}님의 사진 소식'
			post_content = caption if caption else '가족 사진이 새로 업로드되었습니다.'
			should_be_hero = not FamilyPost.objects.filter(is_hero=True).exists()

			new_post = FamilyPost.objects.create(
				title=post_title,
				content=post_content,
				main_image=representative_image,
				event_date=event_date,
				author=request.user,
				is_hero=should_be_hero,
			)
			if captured_at:
				FamilyPost.objects.filter(pk=new_post.pk).update(created_at=captured_at)
			_sync_post_tags(new_post, form.cleaned_data.get('tags'))
			for uploaded_image in extra_images:
				extra_post_image = FamilyPostImage.objects.create(post=new_post, image=uploaded_image)
				if captured_at:
					FamilyPostImage.objects.filter(pk=extra_post_image.pk).update(created_at=captured_at)

			for compressed_video in compressed_videos:
				extra_post_video = FamilyPostVideo.objects.create(post=new_post, video=compressed_video)
				if captured_at:
					FamilyPostVideo.objects.filter(pk=extra_post_video.pk).update(created_at=captured_at)

			messages.success(request, '사진이 업로드되었습니다.')
			return redirect('home')
	else:
		form = FamilyMemberPhotoForm()

	return render(request, 'posts/upload_photo.html', {'form': form})


@login_required
def add_family_member(request):
	if request.user.username != 'bihong':
		return redirect('home')

	if request.method == 'POST':
		form = FamilyMemberCreateForm(request.POST)
		if form.is_valid():
			new_user = form.save()
			emoji = (form.cleaned_data.get('emoji') or '🙂').strip() or '🙂'
			display_name = (form.cleaned_data.get('first_name') or '').strip()
			FamilyMemberProfile.objects.update_or_create(
				user=new_user,
				defaults={
					'emoji': emoji,
					'display_name': display_name,
				},
			)
			messages.success(request, '가족 계정이 추가되었습니다.')
			return redirect('home')
	else:
		form = FamilyMemberCreateForm()

	return render(request, 'posts/add_family_member.html', {'form': form})
