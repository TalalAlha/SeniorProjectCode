"""
Employee invitation URL routes.
Mounted at: /api/v1/employees/
"""
from django.urls import path

from .views import (
    InviteEmployeeView,
    GetInvitationDetailsView,
    AcceptInvitationView,
    ListPendingInvitationsView,
    ResendInvitationView,
    CancelInvitationView,
)

urlpatterns = [
    path('invite/', InviteEmployeeView.as_view(), name='employee_invite'),
    path('invite/<uuid:token>/', GetInvitationDetailsView.as_view(), name='invitation_details'),
    path('invite/<uuid:token>/accept/', AcceptInvitationView.as_view(), name='accept_invitation'),

    # Pending invitation management
    path('pending/', ListPendingInvitationsView.as_view(), name='pending_invitations'),
    path('<int:user_id>/resend/', ResendInvitationView.as_view(), name='resend_invitation'),
    path('<int:user_id>/cancel/', CancelInvitationView.as_view(), name='cancel_invitation'),
]
