"""Users app models."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that uses email as the primary identifier.

    **Fields**:
    - `email`: EmailField, required, unique email address of the user.
    - `username`: CharField, required, unique identifier for the user.
    - `first_name`: CharField, optional, the user's first name.
    - `last_name`: CharField, optional, the user's last name.
    - `is_active`: BooleanField, default=True, indicates if the user account
    is active.
    - `is_staff`: BooleanField, default=False, indicates if the user can log
    into the admin site.
    - `is_superuser`: BooleanField, default=False, indicates if the user has
    all permissions without explicitly assigning them.
    - `last_login`: DateTimeField, optional, the last time the user logged in.
    - `date_joined`: DateTimeField, auto_now_add=True, the date and time when
    the user account was created.
    """

    email = models.EmailField(unique=True, verbose_name='Электронная почта')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        """Meta-data of the User class."""

        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)
