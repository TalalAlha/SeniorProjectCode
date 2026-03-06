"""
Gamification Signals
====================
Django signals for automatic badge awarding and points tracking.

Signal Handlers:
1. QuizResult.save() -> Award quiz-related badges and points
2. TrackingEvent.save() (EMAIL_REPORTED) -> Award phishing reporter badges and points
3. RemediationTraining.save() (PASSED) -> Award training badges and points
4. RiskScore.save() -> Check for "Security Aware" badge
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .services import (
    POINTS_CONFIG,
    award_points,
    calculate_quiz_points,
    check_and_award_badge,
    check_training_champion_badge,
    check_security_aware_badge,
)
from .models import PointsTransaction

logger = logging.getLogger(__name__)


# ============================================================================
# Quiz Result Signals
# ============================================================================

@receiver(post_save, sender='campaigns.QuizResult')
def handle_quiz_result(sender, instance, created, **kwargs):
    """
    Handle quiz completion:
    1. Award points for completion
    2. Check for "First Quiz Completed" badge
    3. Check for "Perfect Quiz Score" badge
    """
    if not created:
        return

    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        with transaction.atomic():
            # Hybrid scoring: 50 base + (score * 0.5) performance bonus
            quiz_score = instance.score or 0
            breakdown = calculate_quiz_points(quiz_score)

            award_points(
                employee=employee,
                transaction_type='QUIZ_COMPLETED',
                points=breakdown['total'],
                source_type='QuizResult',
                source_id=instance.id,
                description=f'Completed quiz: {quiz_score}% score → {breakdown["base_points"]} base + {breakdown["performance_bonus"]} bonus = {breakdown["total"]} pts',
                metadata={
                    'quiz_score': quiz_score,
                    'base_points': breakdown['base_points'],
                    'performance_bonus': breakdown['performance_bonus'],
                    'total_points': breakdown['total'],
                }
            )

            # Check for perfect score badge (badge only, points already in hybrid total)
            if quiz_score == 100:
                check_and_award_badge(
                    employee=employee,
                    badge_type='PERFECT_QUIZ_SCORE',
                    source_type='QuizResult',
                    source_id=instance.id
                )

            # Check for first quiz badge
            from apps.campaigns.models import QuizResult
            quiz_count = QuizResult.objects.filter(employee=employee).count()
            if quiz_count == 1:
                check_and_award_badge(
                    employee=employee,
                    badge_type='FIRST_QUIZ_COMPLETED',
                    source_type='QuizResult',
                    source_id=instance.id
                )

        logger.info(f'Gamification: Processed QuizResult for {employee.email} — {quiz_score}% → {breakdown["total"]} pts')

    except Exception as e:
        logger.error(f'Error in gamification quiz signal: {e}')


# ============================================================================
# Simulation Tracking Event Signals
# ============================================================================

@receiver(post_save, sender='simulations.TrackingEvent')
def handle_tracking_event(sender, instance, created, **kwargs):
    """
    Handle simulation tracking events:
    1. Award points for reporting phishing
    2. Check for "Phish Slayer" badge (5+ reports)
    """
    if not created:
        return

    # Only process EMAIL_REPORTED events
    if instance.event_type != 'EMAIL_REPORTED':
        return

    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        with transaction.atomic():
            # Award points for reporting phishing
            award_points(
                employee=employee,
                transaction_type='PHISHING_REPORTED',
                points=POINTS_CONFIG['PHISHING_REPORTED'],
                source_type='TrackingEvent',
                source_id=instance.id,
                description='Reported phishing simulation email'
            )

            # Check for Phish Slayer badge (5+ reports)
            from apps.simulations.models import TrackingEvent
            report_count = TrackingEvent.objects.filter(
                employee=employee,
                event_type='EMAIL_REPORTED'
            ).count()

            if report_count >= 5:
                check_and_award_badge(
                    employee=employee,
                    badge_type='PHISH_SLAYER',
                    source_type='TrackingEvent',
                    source_id=instance.id
                )

        logger.info(f'Gamification: Processed TrackingEvent (EMAIL_REPORTED) for {employee.email}')

    except Exception as e:
        logger.error(f'Error in gamification tracking signal: {e}')


# ============================================================================
# Remediation Training Signals
# ============================================================================

@receiver(post_save, sender='training.RemediationTraining')
def handle_training_completion(sender, instance, created, **kwargs):
    """
    Handle training completion:
    1. Award points for completing training
    2. Award bonus points for passing
    3. Check for "Quick Learner" badge (passed on first attempt)
    4. Check for "Training Champion" badge (all trainings completed)
    """
    # Only process status changes to PASSED or COMPLETED
    if instance.status not in ['PASSED', 'COMPLETED']:
        return

    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        # Check if we already awarded points for this training
        already_awarded = PointsTransaction.objects.filter(
            employee=employee,
            source_type='RemediationTraining',
            source_id=instance.id,
            transaction_type='TRAINING_COMPLETED'
        ).exists()

        if already_awarded:
            return

        with transaction.atomic():
            # Award base completion points
            award_points(
                employee=employee,
                transaction_type='TRAINING_COMPLETED',
                points=POINTS_CONFIG['TRAINING_COMPLETED'],
                source_type='RemediationTraining',
                source_id=instance.id,
                description=f'Completed training: {instance.training_module.title}'
            )

            # Award bonus points for passing
            if instance.status == 'PASSED':
                award_points(
                    employee=employee,
                    transaction_type='TRAINING_PASSED',
                    points=POINTS_CONFIG['TRAINING_PASSED'],
                    source_type='RemediationTraining',
                    source_id=instance.id,
                    description=f'Passed training: {instance.training_module.title}'
                )

                # Check for Quick Learner badge (passed on first attempt)
                if instance.quiz_attempts == 1:
                    award_points(
                        employee=employee,
                        transaction_type='FIRST_ATTEMPT_PASS',
                        points=POINTS_CONFIG['FIRST_ATTEMPT_PASS'],
                        source_type='RemediationTraining',
                        source_id=instance.id,
                        description='First attempt pass bonus!'
                    )
                    check_and_award_badge(
                        employee=employee,
                        badge_type='QUICK_LEARNER',
                        source_type='RemediationTraining',
                        source_id=instance.id
                    )

            # Check for Training Champion badge
            check_training_champion_badge(employee)

        logger.info(f'Gamification: Processed RemediationTraining for {employee.email}')

    except Exception as e:
        logger.error(f'Error in gamification training signal: {e}')


# ============================================================================
# Risk Score Signals (for Security Aware badge)
# ============================================================================

@receiver(post_save, sender='training.RiskScore')
def handle_risk_score_change(sender, instance, **kwargs):
    """
    Check for "Security Aware" badge:
    - LOW risk score (<=30) maintained for 30+ days
    """
    try:
        employee = instance.employee
        if not employee or employee.role != 'EMPLOYEE':
            return

        # Only check if score is LOW
        if instance.risk_level != 'LOW':
            return

        check_security_aware_badge(employee, instance)

    except Exception as e:
        logger.error(f'Error in gamification risk score signal: {e}')
