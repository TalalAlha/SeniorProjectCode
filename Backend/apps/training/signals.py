"""
Training App Signals
====================
Django signals for automatic risk score updates and remediation training assignment.

Signal Handlers:
1. QuizResult.save() → Update RiskScore with quiz statistics
2. TrackingEvent.save() (LINK_CLICKED, CREDENTIALS_ENTERED) → Update RiskScore
3. RiskScore.save() (if > 70) → Auto-assign RemediationTraining
4. RemediationTraining completion → Update RiskScore statistics
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from datetime import timedelta

from .models import (
    RiskScore,
    RiskScoreHistory,
    TrainingModule,
    RemediationTraining
)


def get_or_create_risk_score(employee):
    """
    Get or create a RiskScore for an employee.
    Returns (risk_score, created) tuple.
    """
    if not employee or not employee.company:
        return None, False

    risk_score, created = RiskScore.objects.get_or_create(
        employee=employee,
        defaults={
            'company': employee.company,
            'score': 50,
            'risk_level': 'MEDIUM'
        }
    )
    return risk_score, created


def create_risk_history(risk_score, event_type, old_score, new_score, old_level,
                        source_type='', source_id=None, description=''):
    """Create a RiskScoreHistory entry."""
    RiskScoreHistory.objects.create(
        risk_score=risk_score,
        employee=risk_score.employee,
        event_type=event_type,
        previous_score=old_score,
        new_score=new_score,
        previous_risk_level=old_level,
        new_risk_level=risk_score.risk_level,
        source_type=source_type,
        source_id=source_id,
        description=description
    )


def auto_assign_remediation(risk_score):
    """
    Auto-assign remediation training if risk score > 70.
    Assigns mandatory training modules that haven't been assigned yet.
    """
    if risk_score.score <= 70:
        return

    # Get mandatory training modules for this company or global
    mandatory_modules = TrainingModule.objects.filter(
        is_active=True,
        is_mandatory=True
    ).filter(
        company__isnull=True
    ) | TrainingModule.objects.filter(
        is_active=True,
        is_mandatory=True,
        company=risk_score.company
    )

    for module in mandatory_modules:
        # Check if already assigned and pending
        exists = RemediationTraining.objects.filter(
            employee=risk_score.employee,
            training_module=module,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).exists()

        if not exists:
            RemediationTraining.objects.create(
                employee=risk_score.employee,
                company=risk_score.company,
                training_module=module,
                assignment_reason='AUTO_HIGH_RISK',
                due_date=timezone.now() + timedelta(days=7),
                source_type='RiskScore',
                source_id=risk_score.id
            )

            # Update module statistics
            module.times_assigned = F('times_assigned') + 1
            module.save(update_fields=['times_assigned'])

            # Update risk score statistics
            risk_score.trainings_assigned = F('trainings_assigned') + 1
            risk_score.save(update_fields=['trainings_assigned'])


@receiver(post_save, sender='campaigns.QuizResult')
def update_risk_score_from_quiz(sender, instance, created, **kwargs):
    """
    Update RiskScore when a QuizResult is created.

    Increases risk score based on:
    - Total questions answered
    - Correct vs incorrect answers
    - Phishing emails missed (false negatives)
    """
    if not created:
        return

    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        risk_score, rs_created = get_or_create_risk_score(employee)
        if not risk_score:
            return

        old_score = risk_score.score
        old_level = risk_score.risk_level

        # Update quiz statistics
        risk_score.total_quizzes_taken = F('total_quizzes_taken') + 1
        risk_score.total_quiz_questions = F('total_quiz_questions') + instance.total_questions
        risk_score.correct_quiz_answers = F('correct_quiz_answers') + instance.correct_answers
        risk_score.phishing_emails_missed = F('phishing_emails_missed') + instance.phishing_emails_missed
        risk_score.last_quiz_date = timezone.now()
        risk_score.save()

        # Refresh to get actual values
        risk_score.refresh_from_db()

        # Recalculate score
        risk_score.recalculate_score()
        risk_score.save()

        # Create history entry
        event_type = 'QUIZ_COMPLETED' if instance.score >= 70 else 'QUIZ_FAILED'
        create_risk_history(
            risk_score=risk_score,
            event_type=event_type,
            old_score=old_score,
            new_score=risk_score.score,
            old_level=old_level,
            source_type='QuizResult',
            source_id=instance.id,
            description=f'Quiz completed with score {instance.score:.1f}%'
        )

        # Auto-assign remediation if needed
        auto_assign_remediation(risk_score)

    except Exception as e:
        # Log error but don't fail the quiz save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error updating risk score from quiz: {e}')


@receiver(post_save, sender='simulations.TrackingEvent')
def update_risk_score_from_simulation(sender, instance, created, **kwargs):
    """
    Update RiskScore when a simulation TrackingEvent is created.

    Handles events:
    - EMAIL_OPENED: Minor increase
    - LINK_CLICKED: Significant increase
    - CREDENTIALS_ENTERED: Major increase
    - EMAIL_REPORTED: Decrease (good behavior)
    """
    if not created:
        return

    # Only process relevant events
    relevant_events = ['EMAIL_OPENED', 'LINK_CLICKED', 'CREDENTIALS_ENTERED', 'EMAIL_REPORTED']
    if instance.event_type not in relevant_events:
        return

    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        risk_score, rs_created = get_or_create_risk_score(employee)
        if not risk_score:
            return

        old_score = risk_score.score
        old_level = risk_score.risk_level

        # Check if total_simulations_received has already been counted
        # for this email simulation. It could have been counted by:
        # 1. A prior relevant tracking event for the same email simulation
        # 2. mark_campaign_emails_sent() which bulk-marks emails as SENT
        #    (detected by: status=SENT + sent_at set + no EMAIL_SENT tracking event)
        from apps.simulations.models import TrackingEvent as SimTrackingEvent
        has_prior_relevant_events = instance.email_simulation and SimTrackingEvent.objects.filter(
            email_simulation=instance.email_simulation,
            event_type__in=['EMAIL_OPENED', 'LINK_CLICKED', 'CREDENTIALS_ENTERED', 'EMAIL_REPORTED']
        ).exclude(id=instance.id).exists()

        was_bulk_marked_sent = (
            instance.email_simulation and
            instance.email_simulation.status == 'SENT' and
            instance.email_simulation.sent_at and
            not SimTrackingEvent.objects.filter(
                email_simulation=instance.email_simulation,
                event_type='EMAIL_SENT'
            ).exists()
        )

        sim_already_counted = has_prior_relevant_events or was_bulk_marked_sent

        # Check if this specific event type was already recorded for this simulation
        def already_has_event(event_type):
            """Check if this email simulation already has this event type."""
            if not instance.email_simulation:
                return False
            return SimTrackingEvent.objects.filter(
                email_simulation=instance.email_simulation,
                event_type=event_type
            ).exclude(id=instance.id).exists()

        # Update based on event type
        if instance.event_type == 'EMAIL_OPENED':
            if not sim_already_counted:
                risk_score.total_simulations_received = F('total_simulations_received') + 1
            if not already_has_event('EMAIL_OPENED'):
                risk_score.simulations_opened = F('simulations_opened') + 1

        elif instance.event_type == 'LINK_CLICKED':
            if not sim_already_counted:
                risk_score.total_simulations_received = F('total_simulations_received') + 1
            if not already_has_event('LINK_CLICKED'):
                risk_score.simulations_clicked = F('simulations_clicked') + 1

        elif instance.event_type == 'CREDENTIALS_ENTERED':
            if not sim_already_counted:
                risk_score.total_simulations_received = F('total_simulations_received') + 1
            if not already_has_event('CREDENTIALS_ENTERED'):
                risk_score.credentials_entered = F('credentials_entered') + 1

        elif instance.event_type == 'EMAIL_REPORTED':
            if not sim_already_counted:
                risk_score.total_simulations_received = F('total_simulations_received') + 1
            if not already_has_event('EMAIL_REPORTED'):
                risk_score.simulations_reported = F('simulations_reported') + 1

        risk_score.last_simulation_date = timezone.now()
        risk_score.save()

        # Refresh and recalculate
        risk_score.refresh_from_db()
        risk_score.recalculate_score()
        risk_score.save()

        # Map event type to history event type
        history_event_map = {
            'EMAIL_OPENED': 'SIMULATION_OPENED',
            'LINK_CLICKED': 'SIMULATION_CLICKED',
            'CREDENTIALS_ENTERED': 'CREDENTIALS_ENTERED',
            'EMAIL_REPORTED': 'PHISHING_REPORTED'
        }

        # Create history entry
        create_risk_history(
            risk_score=risk_score,
            event_type=history_event_map.get(instance.event_type, instance.event_type),
            old_score=old_score,
            new_score=risk_score.score,
            old_level=old_level,
            source_type='TrackingEvent',
            source_id=instance.id,
            description=f'Simulation event: {instance.event_type}'
        )

        # Auto-assign remediation for risky behavior
        if instance.event_type in ['LINK_CLICKED', 'CREDENTIALS_ENTERED']:
            auto_assign_remediation(risk_score)

            # Also assign training specific to the attack vector
            try:
                simulation = instance.email_simulation
                if simulation and simulation.campaign and simulation.campaign.template:
                    attack_vector = simulation.campaign.template.attack_vector

                    # Map attack vectors to training categories
                    vector_to_category = {
                        'LINK_MANIPULATION': 'LINK_SAFETY',
                        'CREDENTIAL_HARVESTING': 'CREDENTIAL_PROTECTION',
                        'MALWARE_ATTACHMENT': 'EMAIL_SECURITY',
                        'SOCIAL_ENGINEERING': 'SOCIAL_ENGINEERING',
                        'BUSINESS_EMAIL_COMPROMISE': 'EMAIL_SECURITY',
                        'SPEAR_PHISHING': 'PHISHING_BASICS',
                    }

                    category = vector_to_category.get(attack_vector)
                    if category:
                        relevant_module = TrainingModule.objects.filter(
                            is_active=True,
                            category=category
                        ).filter(
                            company__isnull=True
                        ).first() or TrainingModule.objects.filter(
                            is_active=True,
                            category=category,
                            company=risk_score.company
                        ).first()

                        if relevant_module:
                            # Check if not already assigned
                            exists = RemediationTraining.objects.filter(
                                employee=employee,
                                training_module=relevant_module,
                                status__in=['ASSIGNED', 'IN_PROGRESS']
                            ).exists()

                            if not exists:
                                RemediationTraining.objects.create(
                                    employee=employee,
                                    company=risk_score.company,
                                    training_module=relevant_module,
                                    assignment_reason='AUTO_SIMULATION_FAIL',
                                    due_date=timezone.now() + timedelta(days=7),
                                    source_type='TrackingEvent',
                                    source_id=instance.id
                                )

                                relevant_module.times_assigned = F('times_assigned') + 1
                                relevant_module.save(update_fields=['times_assigned'])

            except Exception:
                pass  # Continue even if attack-specific training fails

    except Exception as e:
        # Log error but don't fail the tracking save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error updating risk score from simulation: {e}')


@receiver(post_save, sender=RiskScore)
def check_remediation_on_score_change(sender, instance, **kwargs):
    """
    Check if remediation training should be auto-assigned when risk score is saved.
    This catches manual score changes and recalculations.
    """
    # Skip if this is from a signal (avoid recursion)
    if hasattr(instance, '_from_signal'):
        return

    if instance.score > 70 and instance.requires_remediation:
        instance._from_signal = True
        try:
            auto_assign_remediation(instance)
        finally:
            del instance._from_signal
