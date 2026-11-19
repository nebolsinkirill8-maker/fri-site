from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.urls import reverse
from django.utils.html import format_html
from . import ratelimit
from .models import User


class RegistrationForm(UserCreationForm):
    media_fields = forms.MultipleChoiceField(
        label='Что FRI может показать в трансляциях и записях турнира',
        help_text='Выбери данные, которые разрешаешь публиковать на стриминговых платформах и видеохостингах. Telegram, почта и пароль сюда не входят. Выбор добровольный.',
        choices=[
            ('nickname', 'Игровой никнейм'), ('photo', 'Фото профиля'),
            ('steam', 'Ссылка Steam'), ('discord', 'Имя в Discord'),
            ('team', 'Команда'), ('mmr', 'MMR'), ('position', 'Игровая позиция'),
            ('equipment', 'Ответы о микрофоне и веб-камере'),
            ('application', 'Ответы и комментарий в анкете участия'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    privacy_consent = forms.BooleanField(
        label='Даю согласие на обработку моих персональных данных',
        error_messages={'required': 'Без согласия на обработку персональных данных аккаунт создать нельзя.'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['privacy_consent'].help_text = format_html(
            'На условиях <a href="{}" target="_blank" rel="noopener">Политики обработки персональных данных</a>. Если тебе меньше 14 лет, согласие даёт родитель или законный представитель.',
            reverse('privacy'),
        )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Аккаунт с такой почтой уже существует.')
        return email


class RateLimitedLoginMixin:
    """Locks an account after repeated failures and slows down password spraying from one IP."""

    def clean(self):
        email = (self.cleaned_data.get('username') or '').strip().lower()
        ip = ratelimit.client_ip(self.request) if self.request else ''
        if email and (ratelimit.is_limited('login-account', email, ratelimit.LOGIN_PER_ACCOUNT)
                      or ratelimit.is_limited('login-ip', ip, ratelimit.LOGIN_PER_IP)):
            raise forms.ValidationError(ratelimit.LOGIN_LOCKED_MESSAGE, code='rate_limited')
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            if email:
                ratelimit.hit('login-account', email, ratelimit.LOGIN_PER_ACCOUNT)
                ratelimit.hit('login-ip', ip, ratelimit.LOGIN_PER_IP)
            raise
        if email:
            ratelimit.reset('login-account', email, ratelimit.LOGIN_PER_ACCOUNT)
        return cleaned


class EmailAuthenticationForm(RateLimitedLoginMixin, AuthenticationForm):
    username = forms.EmailField(label='Электронная почта', widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}))

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class RateLimitedAdminAuthenticationForm(RateLimitedLoginMixin, AdminAuthenticationForm):
    pass


class ProfileForm(forms.ModelForm):
    photo = forms.ImageField(label='Твой фейс', required=False)

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo or not hasattr(photo, 'content_type'):
            return photo
        if photo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Фото должно быть не больше 10 МБ.')
        from PIL import Image, ImageOps
        from io import BytesIO
        from uuid import uuid4
        from django.core.files.uploadedfile import SimpleUploadedFile
        try:
            image = Image.open(photo)
            if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 20000000:
                raise ValueError
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((1024, 1024))
            output = BytesIO()
            image.save(output, 'JPEG', quality=88)
        except Exception:
            raise forms.ValidationError('Выбери корректное фото JPG, PNG или WebP до 20 мегапикселей.')
        return SimpleUploadedFile(f'{uuid4().hex}.jpg', output.getvalue(), content_type='image/jpeg')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('microphone', 'webcam'):
            self.fields[name].choices = [('', 'Выбери ответ'), *User.Equipment.choices]
            self.fields[name].required = True
            self.fields[name].error_messages['required'] = 'Выбери «Да» или «Нет».'

    class Meta:
        model = User
        fields = ('nickname', 'telegram', 'discord', 'steam_url', 'mmr', 'position', 'microphone', 'webcam', 'photo')
        help_texts = {'telegram': 'Username, например @player_name.', 'discord': 'Имя пользователя Discord.', 'steam_url': 'Ссылка https://steamcommunity.com/id/... или /profiles/...', 'mmr': 'Текущий рейтинг, если известен.'}


class AdminUserCreationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizers creating an account in the CRM cannot consent on the player's behalf.
        del self.fields['privacy_consent']


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
