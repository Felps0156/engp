'''User and account preference models.'''

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from base.models import BaseModel


class UserManager(BaseUserManager):
    '''Create users using a normalized e-mail address as the identifier.'''

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        '''Normalize the complete e-mail address for identity comparisons.'''

        return (email or '').strip().casefold()

    def get_by_natural_key(self, email):
        return self.get(email=self.normalize_email(email))

    async def aget_by_natural_key(self, email):
        return await self.aget(email=self.normalize_email(email))

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário precisa ter is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    '''Application user identified by a unique e-mail address.'''

    username = None
    email = models.EmailField(
        'e-mail',
        unique=True,
        max_length=254,
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'
        ordering = ('email',)

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email)
        return super().save(*args, **kwargs)


def validate_timezone(value):
    '''Validate that a value is an available IANA timezone identifier.'''

    try:
        ZoneInfo(value)
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        raise ValidationError('Informe um fuso horário válido.')


class UserSettings(BaseModel):
    '''Preferences shared by all workspaces belonging to a user.'''

    class Theme(models.TextChoices):
        SYSTEM = 'system', 'Sistema'
        LIGHT = 'light', 'Claro'
        DARK = 'dark', 'Escuro'

    class Language(models.TextChoices):
        PT_BR = 'pt-br', 'Português (Brasil)'

    class DateFormat(models.TextChoices):
        DAY_MONTH_YEAR = 'DD/MM/YYYY', 'DD/MM/AAAA'
        DAY_MONTH_YEAR_SHORT = 'DD/MM/YY', 'DD/MM/AA'
        YEAR_MONTH_DAY = 'YYYY-MM-DD', 'AAAA-MM-DD'

    class TimeFormat(models.TextChoices):
        TWENTY_FOUR_HOUR = '24h', '24 horas (14:30)'
        TWELVE_HOUR = '12h', '12 horas (2:30 PM)'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name='usuário',
    )
    theme = models.CharField(
        'tema',
        max_length=10,
        choices=Theme.choices,
        default=Theme.SYSTEM,
    )
    timezone = models.CharField(
        'fuso horário',
        max_length=64,
        default='America/Sao_Paulo',
        validators=[validate_timezone],
    )
    language = models.CharField(
        'idioma',
        max_length=10,
        choices=Language.choices,
        default=Language.PT_BR,
    )
    date_format = models.CharField(
        'formato de data',
        max_length=12,
        choices=DateFormat.choices,
        default=DateFormat.DAY_MONTH_YEAR,
    )
    time_format = models.CharField(
        'formato de horário',
        max_length=4,
        choices=TimeFormat.choices,
        default=TimeFormat.TWENTY_FOUR_HOUR,
    )
    default_focus_minutes = models.PositiveSmallIntegerField(
        'duração padrão do foco',
        default=25,
        validators=[MinValueValidator(1), MaxValueValidator(180)],
    )
    default_break_minutes = models.PositiveSmallIntegerField(
        'duração padrão da pausa',
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
    )
    focus_end_sound_enabled = models.BooleanField(
        'som ao encerrar o foco',
        default=True,
    )
    onboarding_completed = models.BooleanField(
        'onboarding concluído',
        default=False,
    )

    class Meta:
        verbose_name = 'configuração do usuário'
        verbose_name_plural = 'configurações dos usuários'
        ordering = ('user_id',)

    def __str__(self):
        return f'Configurações de {self.user}'
