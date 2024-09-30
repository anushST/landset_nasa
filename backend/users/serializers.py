"""Serializers of users app."""
import datetime

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework import serializers

from .exceptions import (
    EmailConfirmationTokenExpiredError, EmailConfirmationTokenInvalidError)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model.

    **Fields**:
    - `username`: CharField, required, unique identifier for the user
    (read-only).
    - `email`: EmailField, required, unique email address of the user
    (read-only).
    - `first_name`: CharField, optional, the user's first name.
    - `last_name`: CharField, optional, the user's last name.
    """

    class Meta:
        """Meta-data of UserSerializer class."""

        model = User
        fields = ('username', 'email', 'first_name', 'last_name',)
        read_only_fields = ('username', 'email')


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for refreshing access tokens.

    **Fields**:
    - `refresh`: Required. The refresh token used to generate a
    new access token.
    """

    refresh = serializers.CharField(required=True, help_text='Refresh token')


class LoginSerializer(serializers.Serializer):
    """Serializer for user login.

    **Fields**:
    - `username_or_email`: Required. The username or email of the user.
    - `password`: Required. The password for the user account.
    """

    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for handling user registration.

    **Fields**:
    - `first_name`: User's first name. Required.
    - `last_name`: User's last name. Not required.
    - `email`: Unique email address of the user. Required.
    - `username`: Unique username for the user. Required.
    - `password`: User's password. Required, not returned in responses.
    """

    class Meta:
        """Meta-data of the RegisterSerializer class."""

        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password',)
        extra_kwargs = {
            'password': {'write_only': True}
        }

    @staticmethod
    def create_confirmation_token(user):
        """Create JWT confirmation token to verify the email address."""
        secret_key = settings.SECRET_KEY
        payload = {
            'user_id': user.id,
            'token': default_token_generator.make_token(user),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }

        jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
        return jwt_token

    @staticmethod
    def decode_confirmation_token(jwt_token):
        """Decode JWT confirmation toke to verify the email address."""
        secret_key = settings.SECRET_KEY
        try:
            payload = jwt.decode(jwt_token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise EmailConfirmationTokenExpiredError('Token expired')
        except jwt.InvalidTokenError:
            raise EmailConfirmationTokenInvalidError('Token is invalid')

    def create(self, validated_data: dict):
        """Create a new user.

        Sets their account as inactive
        until email confirmation, and sends a confirmation email.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()

        token = RegisterSerializer.create_confirmation_token(user)
        confirm_url = (f'http://{settings.HOST_NAME}:8000/'
                       f'auth/verify-email/{str(token)}/')

        send_mail(
            'Confirm your email',
            (f'Please confirm your email by clicking the following '
             f'link: {confirm_url}'),
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return user
