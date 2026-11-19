import tempfile
from io import BytesIO
from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import User


class PhotoTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp.name)
        self.override.enable()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.override.disable)
        self.user = User.objects.create_user('photo@example.com', 'test-password-123')
        self.client.force_login(self.user)
        self.data = {'nickname': 'Player', 'microphone': 'yes', 'webcam': 'no'}

    def image(self):
        output = BytesIO()
        Image.new('RGB', (1200, 800), 'red').save(output, 'PNG')
        return SimpleUploadedFile('personal-name.png', output.getvalue(), content_type='image/png')

    def test_optional_and_invalid(self):
        self.assertEqual(self.client.post(reverse('profile_edit'), self.data).status_code, 302)
        self.client.post(reverse('profile_edit'), {**self.data, 'photo': SimpleUploadedFile('bad.jpg', b'not an image', content_type='image/jpeg')})
        self.user.refresh_from_db()
        self.assertFalse(self.user.photo)

    def test_upload_replace_delete_and_private(self):
        self.assertEqual(self.client.post(reverse('profile_edit'), {**self.data, 'photo': self.image()}).status_code, 302)
        self.user.refresh_from_db()
        old = self.user.photo.name
        self.assertNotIn('personal-name', old)
        with Image.open(self.user.photo.path) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(max(image.size), 1024)
            self.assertFalse(image.getexif())
        response = self.client.get(reverse('profile_photo'))
        self.assertEqual(response.status_code, 200)
        b''.join(response.streaming_content)
        response.close()
        self.client.post(reverse('profile_edit'), {**self.data, 'photo': self.image()})
        self.user.refresh_from_db()
        self.assertFalse(self.user.photo.storage.exists(old))
        other = User.objects.create_user('other-photo@example.com', 'test-password-123')
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('profile_photo')).status_code, 404)
        self.client.force_login(self.user)
        self.client.post(reverse('profile_edit'), {**self.data, 'photo-clear': 'on'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.photo)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('profile_photo')).status_code, 302)
