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


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text='Refresh token')


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user registration. It creates a user,
    sends an email confirmation link, and returns the user object.
    """

    class Meta:
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
        """
        This method creates a new user, sets their account as inactive
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
