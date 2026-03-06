import uuid
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.decorators import api_view, permission_classes as fn_permission_classes

from apps.core.emails import send_verification_email, send_employee_invitation, send_password_reset_email

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer
)

logger = logging.getLogger(__name__)

User = get_user_model()

VERIFICATION_TOKEN_EXPIRY_HOURS = 24


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with JWT tokens and user information."""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint — sends a verification email after creation."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email (fire-and-forget; log but don't fail on error)
        try:
            send_verification_email(user, str(user.verification_token))
        except Exception as exc:
            logger.error('Failed to send verification email to %s: %s', user.email, exc)

        return Response({
            'message': (
                'Registration successful! '
                'Please check your email to verify your account before logging in.'
            ),
            'email': user.email,
            'verification_sent': True,
        }, status=status.HTTP_201_CREATED)


class LogoutView(views.APIView):
    """Logout endpoint to blacklist refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        try:
            from apps.notifications.services import NotificationService
            NotificationService.notify_profile_updated(user=instance)
        except Exception as exc:
            logger.warning('Failed to create profile-updated notification: %s', exc)

        return Response(
            UserSerializer(instance).data,
            status=status.HTTP_200_OK
        )


class VerifyEmailView(views.APIView):
    """Confirm email ownership using the UUID token from the verification email."""

    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token.', 'invalid': True},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_verified:
            return Response(
                {'message': 'Email already verified. You can log in now.', 'already_verified': True},
                status=status.HTTP_200_OK,
            )

        token_age = timezone.now() - user.verification_token_created
        if token_age > timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS):
            return Response(
                {
                    'error': 'Verification link has expired. Please request a new one.',
                    'expired': True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.is_active = True  # activates accounts created inactive (e.g. company admins)
        user.save(update_fields=['is_verified', 'is_active'])

        # Send branded welcome email to newly verified company admins
        if user.role == 'COMPANY_ADMIN' and user.company:
            try:
                from apps.core.emails import send_company_welcome_email
                send_company_welcome_email(user, user.company)
            except Exception as exc:
                logger.warning('Failed to send company welcome email to %s: %s', user.email, exc)

        return Response(
            {'message': 'Email verified successfully! You can now log in.', 'verified': True},
            status=status.HTTP_200_OK,
        )


class ResendVerificationView(views.APIView):
    """Issue a fresh verification token and resend the verification email."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response(
                {'error': 'Email address is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether the address is registered (security)
            return Response(
                {'message': 'If this email is registered, a new verification link has been sent.'},
                status=status.HTTP_200_OK,
            )

        if user.is_verified:
            return Response(
                {'message': 'This email is already verified. You can log in now.'},
                status=status.HTTP_200_OK,
            )

        # Rotate token so old links can't be reused
        user.verification_token = uuid.uuid4()
        user.verification_token_created = timezone.now()
        user.save(update_fields=['verification_token', 'verification_token_created'])

        try:
            send_verification_email(user, str(user.verification_token))
        except Exception as exc:
            logger.error('Failed to resend verification email to %s: %s', user.email, exc)
            return Response(
                {'error': 'Failed to send email. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {'message': 'Verification email sent! Please check your inbox.'},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(views.APIView):
    """Change user password endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Set new password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Notify user of password change
        try:
            from apps.notifications.services import NotificationService
            NotificationService.notify_password_changed(user=user)
        except Exception as exc:
            logger.warning('Failed to create password-changed notification: %s', exc)

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


INVITATION_EXPIRY_DAYS = 7


class InviteEmployeeView(views.APIView):
    """Send a token-based invitation email to a new employee."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_company_admin:
            return Response(
                {'error': 'Only company admins can invite employees.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        company = request.user.company
        if not company:
            return Response(
                {'error': 'You are not associated with any company.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = request.data.get('email', '').strip().lower()
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        department = request.data.get('department', '').strip()

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'A user with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation_token = uuid.uuid4()

        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='EMPLOYEE',
            company=company,
            is_active=False,
            is_verified=False,
            invitation_token=invitation_token,
            invitation_sent_at=timezone.now(),
            invitation_status='PENDING',
        )
        user.set_unusable_password()
        user.save(update_fields=['password'])

        # Store department in a custom field if available, otherwise no-op
        # (department is not on User model, it's handled at the employee level)
        # We pass it along in the email context for display purposes.

        try:
            send_employee_invitation(
                inviting_admin=request.user,
                employee_email=email,
                employee_name=f'{first_name} {last_name}'.strip() or email,
                company=company,
                invitation_token=str(invitation_token),
            )
        except Exception as exc:
            logger.error('Failed to send invitation email to %s: %s', email, exc)
            user.delete()
            return Response(
                {'error': 'Failed to send invitation email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'message': 'Invitation sent successfully.',
            'user_id': user.id,
            'email': email,
        }, status=status.HTTP_201_CREATED)


class GetInvitationDetailsView(views.APIView):
    """Return invitation metadata for the accept-invitation page."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user = User.objects.select_related('company').get(invitation_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token.', 'invalid': True},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.invitation_status == 'ACCEPTED':
            return Response(
                {'error': 'This invitation has already been accepted.', 'already_accepted': True},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.invitation_sent_at:
            expiry = user.invitation_sent_at + timedelta(days=INVITATION_EXPIRY_DAYS)
            if timezone.now() > expiry:
                user.invitation_status = 'EXPIRED'
                user.save(update_fields=['invitation_status'])
                return Response(
                    {'error': 'This invitation has expired.', 'expired': True},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'company_name': user.company.name if user.company else '',
            'valid': True,
        })


class AcceptInvitationView(views.APIView):
    """Activate an invited employee account by setting a password."""

    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.select_related('company').get(invitation_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.invitation_status == 'ACCEPTED':
            return Response(
                {'error': 'This invitation has already been accepted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.invitation_sent_at:
            expiry = user.invitation_sent_at + timedelta(days=INVITATION_EXPIRY_DAYS)
            if timezone.now() > expiry:
                user.invitation_status = 'EXPIRED'
                user.save(update_fields=['invitation_status'])
                return Response(
                    {'error': 'This invitation has expired.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        password = request.data.get('password', '')
        if not password:
            return Response({'error': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.is_active = True
        user.is_verified = True
        user.invitation_status = 'ACCEPTED'
        user.invitation_accepted_at = timezone.now()
        user.save(update_fields=[
            'password', 'is_active', 'is_verified',
            'invitation_status', 'invitation_accepted_at',
        ])

        # Welcome notification for new employee + alert admin
        try:
            from apps.notifications.services import NotificationService
            NotificationService.notify_welcome(employee=user)

            if user.company:
                admin = User.objects.filter(
                    company=user.company, role='COMPANY_ADMIN', is_active=True
                ).first()
                if admin:
                    NotificationService.notify_employee_joined(admin=admin, employee=user)
        except Exception as exc:
            logger.warning('Failed to create invitation-accepted notifications: %s', exc)

        return Response({
            'message': 'Invitation accepted! You can now log in.',
            'email': user.email,
        }, status=status.HTTP_200_OK)


class ListPendingInvitationsView(views.APIView):
    """Return all PENDING invitations for the admin's company."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_company_admin:
            return Response(
                {'error': 'Only company admins can view pending invitations.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        company = request.user.company
        if not company:
            return Response(
                {'error': 'You are not associated with any company.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        pending = User.objects.filter(
            company=company,
            invitation_status='PENDING',
        ).order_by('-invitation_sent_at')

        data = [
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'invitation_sent_at': u.invitation_sent_at,
            }
            for u in pending
        ]
        return Response({'results': data})


class ResendInvitationView(views.APIView):
    """Regenerate the invitation token and resend the invitation email."""

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not request.user.is_company_admin:
            return Response(
                {'error': 'Only company admins can resend invitations.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(
                id=user_id,
                company=request.user.company,
                invitation_status='PENDING',
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Pending invitation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.invitation_token = uuid.uuid4()
        user.invitation_sent_at = timezone.now()
        user.save(update_fields=['invitation_token', 'invitation_sent_at'])

        try:
            send_employee_invitation(
                inviting_admin=request.user,
                employee_email=user.email,
                employee_name=f'{user.first_name} {user.last_name}'.strip() or user.email,
                company=request.user.company,
                invitation_token=str(user.invitation_token),
            )
        except Exception as exc:
            logger.error('Failed to resend invitation to %s: %s', user.email, exc)
            return Response(
                {'error': 'Failed to send email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'message': 'Invitation resent successfully.'})


class CancelInvitationView(views.APIView):
    """Cancel a pending invitation and delete the placeholder user account."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        if not request.user.is_company_admin:
            return Response(
                {'error': 'Only company admins can cancel invitations.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(
                id=user_id,
                company=request.user.company,
                invitation_status='PENDING',
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Pending invitation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@fn_permission_classes([AllowAny])
def request_password_reset(request):
    """Send a password reset email (always returns 200 to avoid email enumeration)."""
    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
        user.verification_token = uuid.uuid4()
        user.verification_token_created = timezone.now()
        user.save(update_fields=['verification_token', 'verification_token_created'])

        try:
            send_password_reset_email(user, str(user.verification_token))
        except Exception as exc:
            logger.error('Failed to send password reset email to %s: %s', email, exc)

    except User.DoesNotExist:
        pass  # Don't reveal whether the address is registered

    return Response(
        {'message': 'If this email is registered, a password reset link has been sent.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@fn_permission_classes([AllowAny])
def reset_password(request, token):
    """Reset user password using a previously issued token."""
    try:
        user = User.objects.get(verification_token=token)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid reset token.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if user.verification_token_created:
        expiry = user.verification_token_created + timedelta(hours=24)
        if timezone.now() > expiry:
            return Response(
                {'error': 'Reset link has expired. Please request a new one.', 'expired': True},
                status=status.HTTP_400_BAD_REQUEST,
            )

    new_password = request.data.get('password', '')
    if not new_password:
        return Response(
            {'error': 'Password is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.verification_token = uuid.uuid4()  # Invalidate the used token
    user.save(update_fields=['password', 'verification_token'])

    return Response(
        {'message': 'Password reset successfully! You can now log in.'},
        status=status.HTTP_200_OK,
    )
