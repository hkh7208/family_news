from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from .models import FamilyPost
from .notifications import send_new_post_notification, send_signup_request_notification


@override_settings(
	EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
	DEFAULT_FROM_EMAIL='no-reply@test.local',
	SIGNUP_REQUEST_NOTIFY_EMAIL='hkh7208@poscodx.com',
	SITE_BASE_URL='http://testserver',
)
class NotificationEmailTests(TestCase):
	def _create_test_image(self):
		return SimpleUploadedFile(
			'cover.jpg',
			(
				b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
				b'\xff\xdb\x00C\x00' + b'\x08' * 64 +
				b'\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01'
				b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08'
				b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
				b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xd2\xcf \xff\xd9'
			),
			content_type='image/jpeg',
		)

	def test_send_signup_request_notification(self):
		applicant = User.objects.create_user(
			username='newmember',
			first_name='새가족',
			email='newmember@example.com',
			password='test-pass-1234',
			is_active=False,
		)

		sent = send_signup_request_notification(applicant)

		self.assertTrue(sent)
		self.assertEqual(len(mail.outbox), 1)
		message = mail.outbox[0]
		self.assertIn('회원가입 신청', message.subject)
		self.assertEqual(message.to, ['hkh7208@poscodx.com'])
		self.assertIn('newmember', message.body)
		self.assertIn('newmember@example.com', message.body)

	def test_send_new_post_notification_includes_image_and_content(self):
		author = User.objects.create_user(username='writer', password='test-pass-1234', email='writer@example.com')
		receiver_1 = User.objects.create_user(username='reader1', password='test-pass-1234', email='reader1@example.com')
		receiver_2 = User.objects.create_user(username='reader2', password='test-pass-1234', email='reader2@example.com')
		User.objects.create_user(username='reader3', password='test-pass-1234', email='')
		User.objects.create_user(username='reader4', password='test-pass-1234', email='reader4@example.com', is_active=False)

		post = FamilyPost.objects.create(
			title='새 기사 테스트',
			content='이것은 새 기사 본문입니다.',
			main_image=self._create_test_image(),
			author=author,
		)

		request = RequestFactory().get('/')
		sent_count = send_new_post_notification(post, request=request)

		self.assertEqual(sent_count, 2)
		self.assertEqual(len(mail.outbox), 1)
		message = mail.outbox[0]
		self.assertIn('새 기사 등록', message.subject)
		self.assertEqual(set(message.bcc), {receiver_1.email, receiver_2.email})
		self.assertIn('이것은 새 기사 본문입니다.', message.body)
		self.assertTrue(message.alternatives)
		html_body, mimetype = message.alternatives[0]
		self.assertEqual(mimetype, 'text/html')
		self.assertIn('<img', html_body)
		self.assertIn('/posts/', html_body)
