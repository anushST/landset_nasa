"""Views of users app."""
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    API endpoint for user registration. This view allows new users
    to register with their email, username, and password. After registration,
    it sends a confirmation email to the user with a verification link.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Registration Successful',
                                  RegisterSerializer),
            400: 'Bad Request'
        },
        operation_description="User registration with email verification",
        operation_summary="Register a new user"
    )
    def post(self, request):
        """
        Handle POST requests to register a new user.
        If the registration is successful, the user receives access
        and refresh tokens.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """
    API endpoint for email verification. The user is activated when theys
    visit the confirmation link sent to their email after registration.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
            'token', openapi.IN_PATH,
            description="Token for email verification",
            type=openapi.TYPE_STRING)],
        responses={
            200: 'Email confirmed successfully',
            400: 'Invalid or expired token',
            409: 'Email already confirmed',
        },
        operation_description="Verify email with a confirmation token",
        operation_summary="Email verification"
    )
    def get(self, request, token):
        """
        Handle GET requests to verify a user's email by validating
        the provided token.
        If the token is valid, the user account is activated.
        """
        try:
            data = RegisterSerializer.decode_confirmation_token(token)
            user = User.objects.get(id=data['user_id'])
            if not user.is_active:
                user.is_active = True
                user.save()
                return Response({'message': 'Email confirmed'},
                                status=status.HTTP_200_OK)
            return Response({'message': 'Email already confirmed'},
                            status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({'error': 'Invalid or expired token'},
                            status=status.HTTP_400_BAD_REQUEST)
