'''User model and manager for e-mail based authentication.'''

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
