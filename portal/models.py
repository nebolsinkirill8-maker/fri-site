from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MaxValueValidator
from urllib.parse import urlsplit
import re
from django.db import models
from django.db.models.functions import Lower


def validate_steam_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or parsed.netloc != 'steamcommunity.com'
            or parsed.query or parsed.fragment
            or not re.fullmatch(r'/(id/[A-Za-z0-9_-]+|profiles/[0-9]+)/?', parsed.path)):
        raise ValidationError('Укажите https://steamcommunity.com/id/имя или /profiles/SteamID.')


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=email.strip().lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('Superuser must have staff and superuser permissions.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField('Электронная почта', unique=True)
    nickname = models.CharField('Никнейм', max_length=80, blank=True)
    discord = models.CharField('Discord', max_length=80, blank=True)
    team_name = models.CharField('Название команды', max_length=100, blank=True)
    telegram = models.CharField('Telegram', max_length=33, blank=True, validators=[RegexValidator(r'^@?[A-Za-z][A-Za-z0-9_]{4,31}$', 'Укажите username Telegram (5–32 символа), можно с @.')])
    steam_url = models.URLField('Профиль Steam', blank=True, validators=[validate_steam_url])
    mmr = models.PositiveIntegerField('MMR', blank=True, null=True, validators=[MaxValueValidator(20000)])
    position = models.CharField('Игровая позиция', max_length=1, blank=True, choices=[('1', '1 — Керри'), ('2', '2 — Мидер'), ('3', '3 — Оффлейнер'), ('4', '4 — Поддержка'), ('5', '5 — Полная поддержка')])
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='user_email_case_insensitive_unique')]

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class TournamentSettings(models.Model):
    applications_open = models.BooleanField('Приём заявок открыт', default=False)
    zxc_applications_open = models.BooleanField('Приём заявок ZXC открыт', default=False)
    registration_starts_on = models.DateField('Начало приёма заявок (оба тура)', blank=True, null=True)
    registration_ends_on = models.DateField('Окончание приёма заявок (оба тура)', blank=True, null=True)
    bracket_ready_on = models.DateField('Формирование сетки до', blank=True, null=True)
    zxc_prizes = models.TextField('Призы ZXC', blank=True)
    zxc_format = models.TextField('Формат ZXC', blank=True)
    prize = models.CharField('Призовой фонд', max_length=200, blank=True)
    group_format = models.TextField('Групповой этап', blank=True)
    playoff_format = models.TextField('Плей-офф', blank=True)
    main_event = models.TextField('Основное событие', blank=True)
    twitch_channel = models.CharField('Канал Twitch', max_length=25, default='ceo111kimikiru', validators=[RegexValidator(r'^[a-zA-Z0-9_]+$', 'Укажите только имя канала Twitch.')])
    telegram_url = models.URLField('Telegram', default='https://t.me/firstrussianinternational')
    discord_url = models.URLField('Discord', default='https://discord.gg/qtRGBJMWg8')

    class Meta:
        verbose_name = 'Настройки турнира'
        verbose_name_plural = 'Настройки турнира'

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return 'Командный турнир FRI'


class Stage(models.Model):
    name = models.CharField('Название', max_length=100)
    starts_at = models.DateTimeField('Начало', blank=True, null=True)
    position = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['position', 'pk']
        verbose_name = 'Этап'
        verbose_name_plural = 'Этапы'

    def __str__(self):
        return self.name


class Sponsor(models.Model):
    class Presentation(models.TextChoices):
        STANDARD = 'standard', 'Обычный'
        SUPPORTER = 'supporter', 'Выделенный'
        PARTNER = 'partner', 'Ключевой партнёр'

    name = models.CharField('Название или имя', max_length=150)
    logo_url = models.URLField('Ссылка на логотип', blank=True)
    url = models.URLField('Сайт', blank=True)
    presentation = models.CharField('Оформление', max_length=10, choices=Presentation.choices, default=Presentation.STANDARD)

    class Meta:
        verbose_name = 'Спонсор'
        verbose_name_plural = 'Спонсоры'

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    players = models.ManyToManyField(User, blank=True, related_name='teams', verbose_name='Игроки')
    notes = models.TextField('Внутренние заметки', blank=True)

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def __str__(self):
        return self.name


class Match(models.Model):
    title = models.CharField('Название', max_length=150)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Этап')
    team_a = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_a', verbose_name='Команда A')
    team_b = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_b', verbose_name='Команда B')
    starts_at = models.DateTimeField('Начало', blank=True, null=True)
    result = models.CharField('Результат', max_length=150, blank=True)

    class Meta:
        ordering = ['starts_at', 'pk']
        verbose_name = 'Матч'
        verbose_name_plural = 'Матчи'
        constraints = [models.CheckConstraint(condition=~models.Q(team_a=models.F('team_b')), name='match_distinct_teams')]

    def clean(self):
        if self.team_a_id and self.team_a_id == self.team_b_id:
            raise ValidationError('Выберите две разные команды.')

    def __str__(self):
        return self.title


class TournamentApplication(models.Model):
    class Competition(models.TextChoices):
        TEAM = 'team', 'Командный турнир'
        ZXC = 'zxc', 'ZXC 1 vs 1'

    class Status(models.TextChoices):
        PENDING = 'pending', 'В обработке'
        ACCEPTED = 'accepted', 'Принята'
        REJECTED = 'rejected', 'Отказ'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_applications', verbose_name='Участник')
    competition = models.CharField('Направление', max_length=4, choices=Competition.choices, default=Competition.TEAM)
    nickname = models.CharField('Никнейм', max_length=80)
    steam_url = models.URLField('Профиль Steam', validators=[validate_steam_url])
    telegram = models.CharField('Telegram', max_length=33, blank=True)
    discord = models.CharField('Discord', max_length=80, blank=True)
    team_name = models.CharField('Название команды', max_length=100, blank=True)
    resides_in_russia = models.BooleanField('Подтвердил проживание в России', default=False)
    is_student = models.BooleanField('Подтвердил обучение в школе или колледже', default=False)
    mmr = models.PositiveIntegerField('MMR', null=True, blank=True)
    position = models.CharField('Игровая позиция', max_length=1, blank=True, choices=User._meta.get_field('position').choices)
    comment = models.CharField('Комментарий игрока', max_length=500, blank=True)
    status = models.CharField('Статус', max_length=8, choices=Status.choices, default=Status.PENDING)
    decision_comment = models.CharField('Ответ участнику', max_length=500, blank=True, help_text='Этот текст увидит участник в личном кабинете.')
    created_at = models.DateTimeField('Подана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'Заявка на турнир'
        verbose_name_plural = 'Заявки на турнир'
        constraints = [
            models.UniqueConstraint(fields=('user', 'competition'), name='unique_user_competition_application'),
            models.CheckConstraint(condition=models.Q(competition__in=('team', 'zxc')), name='application_valid_competition'),
            models.CheckConstraint(condition=models.Q(status__in=('pending', 'accepted', 'rejected')), name='tournament_application_valid_status'),
        ]

    def __str__(self):
        return f'{self.nickname} (№{self.pk})'
