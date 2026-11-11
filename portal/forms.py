from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from .models import User


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Аккаунт с такой почтой уже существует.')
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Электронная почта', widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}))

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('nickname', 'telegram', 'discord', 'steam_url', 'team_name', 'mmr', 'position')
        help_texts = {'telegram': 'Username, например @player_name.', 'discord': 'Имя пользователя Discord.', 'team_name': 'Если идёшь с командой, укажи её название. Все игроки команды должны указать одинаковое название.', 'steam_url': 'Ссылка https://steamcommunity.com/id/... или /profiles/...', 'mmr': 'Текущий рейтинг, если известен.'}


class AdminUserCreationForm(RegistrationForm):
    pass


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
