"""Users app models."""
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model."""

    class Meta():
        """Meta-data of the User class."""

        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)
