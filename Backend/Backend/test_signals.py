"""
PhishAware Signal Integration Test Script
Run with: python manage.py shell < test_signals.py
Or copy/paste into: python manage.py shell

This script tests all signal integrations to verify they work correctly.
"""

import sys
from datetime import datetime, timedelta
from django.utils import timezone
import uuid

print("=" * 70)
print("PhishAware Signal Integration Tests")
print("=" * 70)

# ============================================================
# SETUP - Get test data
# ============================================================
print("\n[SETUP] Loading test data...")

from apps.accounts.models import User
from apps.companies.models import Company
from apps.campaigns.models import Campaign, Quiz, QuizResult
from apps.simulations.models import SimulationTemplate, SimulationCampaign, EmailSimulation, TrackingEvent
from apps.training.models import RiskScore, RiskScoreHistory, TrainingModule, RemediationTraining, TrainingQuestion
from apps.gamification.models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints

try:
    company = Company.objects.get(name='Acme Corporation')
    admin = User.objects.get(email='admin@acme.com')
    alice = User.objects.get(email='alice@acme.com')
    print(f"  Company: {company.name}")
    print(f"  Admin: {admin.email}")
    print(f"  Test Employee: {alice.email}")
except Exception as e:
    print(f"ERROR: Test data not found. Run setup_test_data.py first!")
    print(f"Error: {e}")
    sys.exit(1)

# Clear Alice's existing test data for clean test
print("\n[SETUP] Clearing Alice's existing data for clean test...")
RiskScore.objects.filter(employee=alice).delete()
RemediationTraining.objects.filter(employee=alice).delete()
EmployeePoints.objects.filter(employee=alice).delete()
EmployeeBadge.objects.filter(employee=alice).delete()
PointsTransaction.objects.filter(employee=alice).delete()
QuizResult.objects.filter(employee=alice).delete()
Quiz.objects.filter(employee=alice).delete()
EmailSimulation.objects.filter(employee=alice).delete()
print("  Data cleared!")

# ============================================================
# TEST 1: QuizResult → RiskScore Signal
# ============================================================
print("\n" + "=" * 70)
print("TEST 1: QuizResult → RiskScore Signal")
print("=" * 70)

# Create campaign and quiz
campaign = Campaign.objects.create(
    name='Signal Test Campaign',
    company=company,
    created_by=admin,
    num_emails=10,
    phishing_ratio=0.5,
    status='ACTIVE'
)

quiz = Quiz.objects.create(
    campaign=campaign,
    employee=alice,
    status='COMPLETED'
)

print("\n[1.1] Creating QuizResult with LOW score (should trigger high risk)...")

# Create poor quiz result
result = QuizResult.objects.create(
    quiz=quiz,
    employee=alice,
    campaign=campaign,
    total_questions=10,
    correct_answers=3,
    incorrect_answers=7,
    score=30,
    phishing_emails_identified=1,
    phishing_emails_missed=4,
    false_positives=2,
    risk_level='HIGH'
)

print(f"  QuizResult: score={result.score}, missed={result.phishing_emails_missed}")

# Verify RiskScore was created
print("\n[1.2] Verifying RiskScore was created/updated...")
try:
    risk = RiskScore.objects.get(employee=alice)
    print(f"  ✓ RiskScore exists: score={risk.score}, level={risk.risk_level}")
    print(f"  ✓ Quizzes tracked: {risk.total_quizzes_taken}")
    print(f"  ✓ Phishing missed: {risk.phishing_emails_missed}")
    print(f"  ✓ Requires remediation: {risk.requires_remediation}")
except RiskScore.DoesNotExist:
    print("  ✗ FAILED: RiskScore was NOT created!")

# Verify RiskScoreHistory
print("\n[1.3] Verifying RiskScoreHistory was created...")
history = RiskScoreHistory.objects.filter(employee=alice)
print(f"  History entries: {history.count()}")
for h in history:
    print(f"    - {h.event_type}: {h.previous_score} → {h.new_score}")

# ============================================================
# TEST 2: QuizResult → Gamification Signal
# ============================================================
print("\n" + "=" * 70)
print("TEST 2: QuizResult → Gamification Signal")
print("=" * 70)

print("\n[2.1] Verifying points were awarded for quiz...")
try:
    points = EmployeePoints.objects.get(employee=alice)
    print(f"  ✓ EmployeePoints exists: total={points.total_points}")
except EmployeePoints.DoesNotExist:
    print("  ✗ FAILED: EmployeePoints was NOT created!")

print("\n[2.2] Verifying FIRST_QUIZ_COMPLETED badge...")
first_quiz_badge = EmployeeBadge.objects.filter(employee=alice, badge__badge_type='FIRST_QUIZ_COMPLETED')
if first_quiz_badge.exists():
    print(f"  ✓ Badge awarded: {first_quiz_badge.first().badge.name}")
else:
    print("  ✗ FAILED: FIRST_QUIZ_COMPLETED badge NOT awarded!")

print("\n[2.3] Checking point transactions...")
transactions = PointsTransaction.objects.filter(employee=alice)
print(f"  Transactions: {transactions.count()}")
for t in transactions:
    print(f"    - {t.transaction_type}: {t.points} pts - {t.description[:50]}")

# ============================================================
# TEST 3: High Risk → Auto-Remediation Signal
# ============================================================
print("\n" + "=" * 70)
print("TEST 3: High Risk → Auto-Remediation Signal")
print("=" * 70)

print("\n[3.1] Checking if training was auto-assigned (score > 70)...")
risk = RiskScore.objects.get(employee=alice)

if risk.score > 70 and risk.requires_remediation:
    trainings = RemediationTraining.objects.filter(employee=alice)
    if trainings.exists():
        print(f"  ✓ Auto-assigned trainings: {trainings.count()}")
        for t in trainings:
            print(f"    - {t.training_module.title} ({t.assignment_reason})")
    else:
        print("  ✗ FAILED: No trainings auto-assigned despite high risk!")
else:
    print(f"  ℹ Risk score ({risk.score}) not above 70, no auto-remediation expected")

# ============================================================
# TEST 4: TrackingEvent → RiskScore Signal
# ============================================================
print("\n" + "=" * 70)
print("TEST 4: TrackingEvent → RiskScore Signal")
print("=" * 70)

print("\n[4.1] Creating simulation data...")
template = SimulationTemplate.objects.first()
if not template:
    print("  ✗ No SimulationTemplate found! Create one first.")
else:
    sim_campaign = SimulationCampaign.objects.create(
        name='Signal Test Simulation',
        company=company,
        template=template,
        created_by=admin,
        status='IN_PROGRESS'
    )

    email_sim = EmailSimulation.objects.create(
        campaign=sim_campaign,
        employee=alice,
        tracking_token=uuid.uuid4(),
        link_token=uuid.uuid4().hex[:32],
        recipient_email=alice.email,
        status='DELIVERED'
    )
    print(f"  ✓ EmailSimulation created: token={email_sim.link_token[:8]}...")

    # Record risk score before
    risk_before = RiskScore.objects.get(employee=alice).score
    clicks_before = RiskScore.objects.get(employee=alice).simulations_clicked

    print("\n[4.2] Creating LINK_CLICKED TrackingEvent...")
    event = TrackingEvent.objects.create(
        email_simulation=email_sim,
        campaign=sim_campaign,
        employee=alice,
        event_type='LINK_CLICKED',
        ip_address='192.168.1.100',
        user_agent='TestBrowser/1.0'
    )
    print(f"  ✓ TrackingEvent created: {event.event_type}")

    # Verify risk score updated
    print("\n[4.3] Verifying RiskScore was updated...")
    risk = RiskScore.objects.get(employee=alice)
    print(f"  Risk score: {risk_before} → {risk.score} (change: {risk.score - risk_before:+d})")
    print(f"  Simulations clicked: {clicks_before} → {risk.simulations_clicked}")

    if risk.simulations_clicked > clicks_before:
        print("  ✓ Simulation click tracked!")
    else:
        print("  ✗ FAILED: Simulation click NOT tracked!")

# ============================================================
# TEST 5: TrackingEvent (Report) → Gamification Signal
# ============================================================
print("\n" + "=" * 70)
print("TEST 5: TrackingEvent (Report) → Gamification Signal")
print("=" * 70)

print("\n[5.1] Recording points before...")
points_before = EmployeePoints.objects.get(employee=alice).total_points

print("\n[5.2] Creating EMAIL_REPORTED TrackingEvent...")
# Create new email simulation for report
email_sim2 = EmailSimulation.objects.create(
    campaign=sim_campaign,
    employee=alice,
    tracking_token=uuid.uuid4(),
    link_token=uuid.uuid4().hex[:32],
    recipient_email=alice.email,
    status='DELIVERED'
)

report_event = TrackingEvent.objects.create(
    email_simulation=email_sim2,
    campaign=sim_campaign,
    employee=alice,
    event_type='EMAIL_REPORTED',
    ip_address='192.168.1.100',
    user_agent='TestBrowser/1.0'
)
print(f"  ✓ Report event created")

print("\n[5.3] Verifying points awarded for reporting...")
points = EmployeePoints.objects.get(employee=alice)
print(f"  Points: {points_before} → {points.total_points} (change: {points.total_points - points_before:+d})")

if points.total_points > points_before:
    print("  ✓ Points awarded for reporting!")
else:
    print("  ✗ FAILED: Points NOT awarded for reporting!")

# ============================================================
# TEST 6: Training Completion → Signals
# ============================================================
print("\n" + "=" * 70)
print("TEST 6: Training Completion → Points & Badges Signal")
print("=" * 70)

print("\n[6.1] Manually assigning training...")
module = TrainingModule.objects.first()
if not module:
    print("  ✗ No TrainingModule found!")
else:
    training = RemediationTraining.objects.create(
        employee=alice,
        company=company,
        training_module=module,
        status='ASSIGNED',
        assignment_reason='MANUAL_ADMIN',
        assigned_by=admin,
        risk_score_before=RiskScore.objects.get(employee=alice).score
    )
    print(f"  ✓ Training assigned: {module.title}")

    print("\n[6.2] Starting training...")
    training.start_training()
    print(f"  Status: {training.status}")

    print("\n[6.3] Marking content viewed...")
    training.mark_content_viewed()
    print(f"  Content viewed: {training.content_viewed}")

    print("\n[6.4] Recording state before quiz submission...")
    points_before = EmployeePoints.objects.get(employee=alice).total_points
    risk_before = RiskScore.objects.get(employee=alice).score
    badges_before = EmployeeBadge.objects.filter(employee=alice).count()

    print("\n[6.5] Submitting quiz with correct answers...")
    questions = TrainingQuestion.objects.filter(module=module, is_active=True)
    answers = [
        {'question_id': q.id, 'selected_answer_index': q.correct_answer_index}
        for q in questions
    ]
    training.submit_quiz(answers)

    print(f"  Quiz score: {training.quiz_score}%")
    print(f"  Status: {training.status}")
    print(f"  Risk score after: {training.risk_score_after}")

    print("\n[6.6] Verifying signal effects...")
    points = EmployeePoints.objects.get(employee=alice)
    risk = RiskScore.objects.get(employee=alice)
    badges = EmployeeBadge.objects.filter(employee=alice).count()

    print(f"  Points: {points_before} → {points.total_points} (change: {points.total_points - points_before:+d})")
    print(f"  Risk: {risk_before} → {risk.score} (change: {risk.score - risk_before:+d})")
    print(f"  Badges: {badges_before} → {badges}")

    if points.total_points > points_before:
        print("  ✓ Points awarded for training completion!")
    else:
        print("  ✗ Points NOT awarded for training completion!")

    # Check for Quick Learner badge
    quick_learner = EmployeeBadge.objects.filter(employee=alice, badge__badge_type='QUICK_LEARNER')
    if quick_learner.exists():
        print("  ✓ QUICK_LEARNER badge awarded (first attempt pass)!")
    else:
        print("  ℹ QUICK_LEARNER badge not awarded (may not be first attempt)")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY - Alice's Current State")
print("=" * 70)

risk = RiskScore.objects.get(employee=alice)
points = EmployeePoints.objects.get(employee=alice)
badges = EmployeeBadge.objects.filter(employee=alice)
trainings = RemediationTraining.objects.filter(employee=alice)
transactions = PointsTransaction.objects.filter(employee=alice)
history = RiskScoreHistory.objects.filter(employee=alice)

print(f"""
Risk Score:
  - Current Score: {risk.score}
  - Risk Level: {risk.risk_level}
  - Requires Remediation: {risk.requires_remediation}
  - History Events: {history.count()}

Gamification:
  - Total Points: {points.total_points}
  - Weekly Points: {points.weekly_points}
  - Badge Count: {points.badge_count}
  - Transactions: {transactions.count()}

Badges Earned: {badges.count()}""")
for b in badges:
    print(f"  - {b.badge.name} ({b.badge.rarity})")

print(f"""
Trainings:
  - Total Assigned: {trainings.count()}
  - Completed/Passed: {trainings.filter(status__in=['COMPLETED', 'PASSED']).count()}
""")

print("=" * 70)
print("SIGNAL INTEGRATION TESTS COMPLETE!")
print("=" * 70)
print("\nIf all tests show ✓, your signals are working correctly.")
print("If any tests show ✗, check the signal configuration in apps/*/signals.py")
