# PhishAware Backend - Comprehensive Testing Guide

This guide provides step-by-step instructions to test all 4 modules of the PhishAware phishing awareness platform.

---

## Table of Contents

1. [Database Setup & Migrations](#1-database-setup--migrations)
2. [Create Test Data via Django Admin](#2-create-test-data-via-django-admin)
3. [API Testing with curl](#3-api-testing-with-curl)
4. [Verify Signal Integration](#4-verify-signal-integration)
5. [End-to-End Test Workflow](#5-end-to-end-test-workflow)
6. [Troubleshooting Guide](#6-troubleshooting-guide)

---

## 1. Database Setup & Migrations

### 1.1 Run All Migrations

Open your terminal in the Backend directory and run:

```bash
# Step 1: Make migrations for all apps (if not already done)
python manage.py makemigrations accounts companies campaigns assessments simulations training gamification

# Step 2: Apply all migrations
python manage.py migrate

# Step 3: Verify migrations succeeded
python manage.py showmigrations
```

**Expected Output for `showmigrations`:**
```
accounts
 [X] 0001_initial
admin
 [X] 0001_initial
 [X] 0002_logentry_remove_auto_add
 [X] 0003_logentry_add_action_flag_choices
assessments
 [X] 0001_initial
 [X] 0002_initial
auth
 [X] 0001_initial
 ...
campaigns
 [X] 0001_initial
companies
 [X] 0001_initial
gamification
 [X] 0001_initial
 [X] 0002_initial_badges
simulations
 [X] 0001_initial
token_blacklist
 [X] 0001_initial
 ...
training
 [X] 0001_initial
```

All items should have `[X]` indicating they are applied.

### 1.2 Verify All Tables Created

```bash
# Use Django shell to check tables
python manage.py shell
```

In the shell, run:

```python
from django.db import connection

# Get all table names
tables = connection.introspection.table_names()
print("\n=== All Database Tables ===")
for t in sorted(tables):
    print(f"  - {t}")

# Check expected tables exist
expected_tables = [
    'accounts_user',
    'companies_company',
    'campaigns_campaign',
    'campaigns_quiz',
    'campaigns_quizresult',
    'assessments_emailtemplate',
    'assessments_quizquestion',
    'simulations_simulationtemplate',
    'simulations_simulationcampaign',
    'simulations_emailsimulation',
    'simulations_trackingevent',
    'training_riskscore',
    'training_riskscorehistory',
    'training_trainingmodule',
    'training_trainingquestion',
    'training_remediationtraining',
    'training_trainingquizanswer',
    'gamification_badge',
    'gamification_employeebadge',
    'gamification_pointstransaction',
    'gamification_employeepoints',
]

print("\n=== Verifying Required Tables ===")
missing = [t for t in expected_tables if t not in tables]
if missing:
    print(f"MISSING TABLES: {missing}")
else:
    print("All required tables exist!")

exit()
```

---

## 2. Create Test Data via Django Admin

### 2.1 Create Superuser

```bash
python manage.py createsuperuser
```

Enter the following when prompted:
- Email: `admin@phishaware.com`
- First name: `Super`
- Last name: `Admin`
- Password: `AdminPass123!`

### 2.2 Start Development Server

```bash
python manage.py runserver
```

Access Django Admin at: http://localhost:8000/admin/

Login with your superuser credentials.

### 2.3 Create Test Company

1. Go to **Companies** > **Companies** > **Add Company**
2. Fill in:
   - Name: `Acme Corporation`
   - Name (Arabic): `شركة أكمي`
   - Description: `Test company for PhishAware testing`
   - Description (Arabic): `شركة تجريبية لاختبار PhishAware`
   - Email: `contact@acme.com`
   - Phone: `+1234567890`
   - Industry: `Technology`
   - Company size: `51-200`
   - Is active: ✓ Checked
   - Subscription start date: Today's date
   - Subscription end date: 1 year from today
3. Click **Save**

### 2.4 Create Test Users

**Company Admin:**
1. Go to **Accounts** > **Users** > **Add User**
2. Fill in:
   - Email: `admin@acme.com`
   - First name: `John`
   - Last name: `Manager`
   - Role: `Company Admin`
   - Company: `Acme Corporation`
   - Password: `TestPass123!`
   - Is active: ✓ Checked
   - Is verified: ✓ Checked
3. Click **Save**

**Employees (Create 3):**

| Email | First Name | Last Name | Role | Company |
|-------|------------|-----------|------|---------|
| `alice@acme.com` | Alice | Smith | Employee | Acme Corporation |
| `bob@acme.com` | Bob | Johnson | Employee | Acme Corporation |
| `carol@acme.com` | Carol | Williams | Employee | Acme Corporation |

Use password `TestPass123!` for all.

### 2.5 Create Simulation Templates

Go to **Simulations** > **Simulation templates** > **Add Simulation Template**

**Template 1 - IT Support Phishing:**
```
Name: IT Support Password Reset
Name (Arabic): إعادة تعيين كلمة المرور من الدعم التقني
Description: Fake IT support password reset request
Sender name: IT Helpdesk
Sender email: helpdesk@acme-support.com
Reply to email: helpdesk@acme-support.com
Subject: Urgent: Your Password Will Expire in 24 Hours
Body HTML:
    <html>
    <body>
    <p>Dear {{employee_name}},</p>
    <p>Your password will expire in 24 hours. Please click the link below to update your password immediately:</p>
    <p><a href="{{phishing_link}}">Reset Password Now</a></p>
    <p>Failure to update your password will result in account lockout.</p>
    <p>Best regards,<br>IT Helpdesk</p>
    </body>
    </html>
Body plain: Dear {{employee_name}}, Your password expires in 24 hours. Click here to reset: {{phishing_link}}
Attack vector: Credential Harvesting
Difficulty: Easy
Requires landing page: ✓ Checked
Landing page title: Password Reset Portal
Landing page message: This was a phishing simulation. In a real attack, your credentials would have been stolen.
Landing page message (Arabic): كانت هذه محاكاة للتصيد. في هجوم حقيقي، كانت بياناتك ستُسرق.
Is active: ✓ Checked
Is public: ✓ Checked
```

**Template 2 - Prize Scam:**
```
Name: Prize Winner Notification
Name (Arabic): إشعار الفائز بالجائزة
Description: Fake lottery/prize notification
Sender name: Rewards Department
Sender email: rewards@prize-center.com
Subject: Congratulations! You've Won a $500 Gift Card!
Body HTML:
    <html>
    <body>
    <p>Dear {{employee_name}},</p>
    <p>You have been randomly selected to receive a $500 gift card!</p>
    <p><a href="{{phishing_link}}">Claim Your Prize Now</a></p>
    <p>This offer expires in 24 hours.</p>
    </body>
    </html>
Attack vector: Prize/Lottery
Difficulty: Easy
Is active: ✓ Checked
Is public: ✓ Checked
```

**Template 3 - CEO Fraud (BEC):**
```
Name: CEO Urgent Request
Name (Arabic): طلب عاجل من الرئيس التنفيذي
Description: Business Email Compromise - CEO impersonation
Sender name: Michael Thompson (CEO)
Sender email: m.thompson@acme-corp.net
Subject: Quick favor - time sensitive
Body HTML:
    <html>
    <body>
    <p>Hi {{employee_name}},</p>
    <p>I'm in a meeting and need you to handle something urgently. Please click the link below to review and approve the attached invoice.</p>
    <p><a href="{{phishing_link}}">Review Invoice</a></p>
    <p>Thanks,<br>Michael</p>
    <p><small>Sent from my iPhone</small></p>
    </body>
    </html>
Attack vector: Business Email Compromise
Difficulty: Medium
Is active: ✓ Checked
Is public: ✓ Checked
```

### 2.6 Create Training Modules

Go to **Training** > **Training modules** > **Add Training Module**

**Module 1 - Phishing Basics:**
```
Title: Introduction to Phishing Attacks
Title (Arabic): مقدمة في هجمات التصيد
Description: Learn the basics of identifying phishing emails
Content type: Text
Category: Phishing Basics
Difficulty: Beginner
Content HTML:
    <h1>What is Phishing?</h1>
    <p>Phishing is a type of social engineering attack where attackers attempt to steal sensitive information by disguising themselves as trustworthy entities.</p>
    <h2>Common Signs of Phishing</h2>
    <ul>
        <li>Urgent language creating panic</li>
        <li>Suspicious sender email addresses</li>
        <li>Generic greetings instead of your name</li>
        <li>Spelling and grammar errors</li>
        <li>Requests for sensitive information</li>
        <li>Suspicious links or attachments</li>
    </ul>
Duration minutes: 15
Passing score: 80
Min questions required: 5
Score reduction on pass: 15
Is active: ✓ Checked
Is mandatory: ✓ Checked
```

After saving, add 5 questions to this module.

**Training Questions for Module 1:**

Go to **Training** > **Training questions** > **Add Training Question**

| Question # | Question Text | Options (JSON) | Correct Answer Index |
|------------|--------------|----------------|---------------------|
| 1 | What is phishing? | `["A fishing technique", "A cyber attack to steal credentials", "A software update", "A firewall setting"]` | 1 |
| 2 | Which is a common sign of a phishing email? | `["Professional formatting", "Urgent language creating panic", "Company logo present", "Proper grammar"]` | 1 |
| 3 | What should you do if you receive a suspicious email? | `["Click the link to verify", "Reply asking for more info", "Report it to IT security", "Forward it to colleagues"]` | 2 |
| 4 | Attackers often impersonate which entities? | `["Random strangers", "Trusted organizations like banks or IT", "Unknown foreign companies", "Social media influencers"]` | 1 |
| 5 | What is the safest action when unsure about an email? | `["Open attachments to check", "Click links to verify", "Contact the sender through official channels", "Ignore it completely"]` | 2 |

**Module 2 - Link Safety:**
```
Title: Identifying Malicious Links
Title (Arabic): التعرف على الروابط الخبيثة
Category: Link Safety
Difficulty: Intermediate
Duration minutes: 20
Passing score: 80
Is active: ✓ Checked
Is mandatory: ✓ Checked
```

Add 5 questions similarly.

**Module 3 - Credential Protection:**
```
Title: Protecting Your Credentials
Title (Arabic): حماية بياناتك الاعتمادية
Category: Credential Protection
Difficulty: Intermediate
Duration minutes: 25
Passing score: 80
Is active: ✓ Checked
Is mandatory: ✓ Checked
```

### 2.7 Verify Badges Were Created

Go to **Gamification** > **Badges**

You should see 6 pre-created badges from the migration:
1. First Quiz Champion (FIRST_QUIZ_COMPLETED)
2. Perfect Score (PERFECT_QUIZ_SCORE)
3. Phish Slayer (PHISH_SLAYER)
4. Quick Learner (QUICK_LEARNER)
5. Training Champion (TRAINING_CHAMPION)
6. Security Aware (SECURITY_AWARE)

If badges are missing, create them manually or run:

```bash
python manage.py shell
```

```python
from apps.gamification.models import Badge

badges_data = [
    {
        'name': 'First Quiz Champion',
        'name_ar': 'بطل الاختبار الأول',
        'badge_type': 'FIRST_QUIZ_COMPLETED',
        'description': 'Complete your first security awareness quiz',
        'description_ar': 'أكمل أول اختبار للتوعية الأمنية',
        'icon': 'trophy',
        'color': '#FFD700',
        'rarity': 'COMMON',
        'points_awarded': 10,
        'is_active': True,
    },
    {
        'name': 'Perfect Score',
        'name_ar': 'الدرجة الكاملة',
        'badge_type': 'PERFECT_QUIZ_SCORE',
        'description': 'Score 100% on any quiz',
        'description_ar': 'احصل على 100% في أي اختبار',
        'icon': 'star',
        'color': '#FFD700',
        'rarity': 'RARE',
        'points_awarded': 50,
        'is_active': True,
    },
    {
        'name': 'Phish Slayer',
        'name_ar': 'قاتل التصيد',
        'badge_type': 'PHISH_SLAYER',
        'description': 'Report 5 or more phishing attempts',
        'description_ar': 'أبلغ عن 5 محاولات تصيد أو أكثر',
        'icon': 'shield',
        'color': '#4CAF50',
        'rarity': 'EPIC',
        'points_awarded': 75,
        'is_active': True,
    },
    {
        'name': 'Quick Learner',
        'name_ar': 'المتعلم السريع',
        'badge_type': 'QUICK_LEARNER',
        'description': 'Pass training on first attempt',
        'description_ar': 'اجتز التدريب من المحاولة الأولى',
        'icon': 'bolt',
        'color': '#2196F3',
        'rarity': 'UNCOMMON',
        'points_awarded': 25,
        'is_active': True,
    },
    {
        'name': 'Training Champion',
        'name_ar': 'بطل التدريب',
        'badge_type': 'TRAINING_CHAMPION',
        'description': 'Complete all assigned trainings',
        'description_ar': 'أكمل جميع التدريبات المعينة',
        'icon': 'medal',
        'color': '#9C27B0',
        'rarity': 'EPIC',
        'points_awarded': 100,
        'is_active': True,
    },
    {
        'name': 'Security Aware',
        'name_ar': 'الوعي الأمني',
        'badge_type': 'SECURITY_AWARE',
        'description': 'Maintain LOW risk level for 30 days',
        'description_ar': 'حافظ على مستوى مخاطر منخفض لمدة 30 يوم',
        'icon': 'verified',
        'color': '#00BCD4',
        'rarity': 'LEGENDARY',
        'points_awarded': 150,
        'is_active': True,
    },
]

for badge_data in badges_data:
    Badge.objects.get_or_create(
        badge_type=badge_data['badge_type'],
        defaults=badge_data
    )

print(f"Total badges: {Badge.objects.count()}")
exit()
```

---

## 3. API Testing with curl

### 3.1 Setup - Get Authentication Token

**Register a New User (Optional):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"testuser@acme.com\", \"password\": \"TestPass123!\", \"first_name\": \"Test\", \"last_name\": \"User\"}"
```

**Login and Get JWT Token:**

For Admin:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"admin@acme.com\", \"password\": \"TestPass123!\"}"
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLC...(long token)",
  "refresh": "eyJ0eXAiOiJKV1QiLC...(long token)",
  "user": {
    "id": 2,
    "email": "admin@acme.com",
    "first_name": "John",
    "last_name": "Manager",
    "role": "COMPANY_ADMIN",
    "company": 1
  }
}
```

**Save the access token for subsequent requests:**
```bash
set ACCESS_TOKEN=eyJ0eXAiOiJKV1QiLC...your_token_here
```

Or on PowerShell:
```powershell
$ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLC...your_token_here"
```

**Login as Employee (Alice):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"alice@acme.com\", \"password\": \"TestPass123!\"}"
```

Save Alice's token:
```bash
set EMPLOYEE_TOKEN=eyJ0eXAiOiJKV1QiLC...alice_token_here
```

### 3.2 Test Profile Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%"
```

### 3.3 Module A - Quiz Campaign Testing

**Step 1: Create a Campaign (as Company Admin):**
```bash
curl -X POST http://localhost:8000/api/v1/campaigns/campaigns/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"Q1 Security Assessment\", \"name_ar\": \"تقييم الأمان للربع الأول\", \"description\": \"Quarterly security awareness quiz\", \"num_emails\": 10, \"phishing_ratio\": 0.5, \"status\": \"ACTIVE\"}"
```

**Expected Response:**
```json
{
  "id": 1,
  "name": "Q1 Security Assessment",
  "status": "ACTIVE",
  ...
}
```

Note the campaign `id` (e.g., 1).

**Step 2: Create Email Templates for Campaign:**
```bash
curl -X POST http://localhost:8000/api/v1/assessments/email-templates/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"campaign\": 1, \"sender_name\": \"IT Support\", \"sender_email\": \"support@company.com\", \"subject\": \"Password Reset Required\", \"body\": \"Click here to reset your password: http://malicious-link.com\", \"email_type\": \"PHISHING\", \"category\": \"CREDENTIAL_HARVESTING\", \"difficulty\": \"EASY\"}"
```

Create 5 phishing and 5 legitimate templates (matching the 10 emails, 50% phishing ratio).

**Step 3: Create Quiz for Employee (Alice):**
```bash
curl -X POST http://localhost:8000/api/v1/campaigns/quizzes/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"campaign\": 1, \"employee\": 3}"
```

Note: Replace `3` with Alice's actual user ID.

**Step 4: Employee Starts Quiz:**
```bash
curl -X PATCH http://localhost:8000/api/v1/campaigns/quizzes/1/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"IN_PROGRESS\"}"
```

**Step 5: Submit Quiz Answers:**
```bash
curl -X POST http://localhost:8000/api/v1/campaigns/quizzes/1/submit/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"answers\": [{\"question_id\": 1, \"answer\": \"PHISHING\"}, {\"question_id\": 2, \"answer\": \"LEGITIMATE\"}]}"
```

### 3.4 Module B - Simulation Campaign Testing

**Step 1: List Available Templates:**
```bash
curl -X GET http://localhost:8000/api/v1/simulations/templates/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%"
```

**Step 2: Create Simulation Campaign:**
```bash
curl -X POST http://localhost:8000/api/v1/simulations/campaigns/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"February Phishing Test\", \"name_ar\": \"اختبار التصيد لشهر فبراير\", \"description\": \"Monthly phishing simulation\", \"template\": 1, \"status\": \"DRAFT\", \"target_all_employees\": true, \"track_email_opens\": true, \"track_link_clicks\": true}"
```

**Step 3: Test Tracking Endpoints (Public - No Auth Required):**

First, get the tracking tokens from an EmailSimulation record:
```bash
curl -X GET http://localhost:8000/api/v1/simulations/emails/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%"
```

Note the `tracking_token` and `link_token` values.

**Track Email Open (simulates tracking pixel):**
```bash
curl -X GET "http://localhost:8000/api/v1/simulations/track/YOUR_TRACKING_TOKEN/"
```

**Track Link Click:**
```bash
curl -X GET "http://localhost:8000/api/v1/simulations/link/YOUR_LINK_TOKEN/"
```

**View Landing Page:**
```bash
curl -X GET "http://localhost:8000/api/v1/simulations/landing/YOUR_LINK_TOKEN/"
```

**Report Phishing:**
```bash
curl -X POST "http://localhost:8000/api/v1/simulations/report/YOUR_LINK_TOKEN/"
```

### 3.5 Module C - Risk Score & Training Testing

**Step 1: View Employee Risk Score (as Admin):**
```bash
curl -X GET http://localhost:8000/api/v1/training/risk-scores/ ^
  -H "Authorization: Bearer %ACCESS_TOKEN%"
```

**Step 2: Employee Views Own Risk Score:**
```bash
curl -X GET http://localhost:8000/api/v1/training/risk-scores/my_score/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 3: List Training Modules:**
```bash
curl -X GET http://localhost:8000/api/v1/training/modules/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 4: Check Employee's Training Assignments:**
```bash
curl -X GET http://localhost:8000/api/v1/training/assignments/my_trainings/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 5: Start Assigned Training:**
```bash
curl -X POST http://localhost:8000/api/v1/training/assignments/1/start/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 6: Mark Content as Viewed:**
```bash
curl -X POST http://localhost:8000/api/v1/training/assignments/1/view_content/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 7: Get Quiz Questions:**
```bash
curl -X GET http://localhost:8000/api/v1/training/assignments/1/quiz/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 8: Submit Training Quiz:**
```bash
curl -X POST http://localhost:8000/api/v1/training/assignments/1/submit_quiz/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"answers\": [{\"question_id\": 1, \"selected_answer_index\": 1}, {\"question_id\": 2, \"selected_answer_index\": 1}, {\"question_id\": 3, \"selected_answer_index\": 2}, {\"question_id\": 4, \"selected_answer_index\": 1}, {\"question_id\": 5, \"selected_answer_index\": 2}]}"
```

### 3.6 Module D - Gamification Testing

**Step 1: View Available Badges:**
```bash
curl -X GET http://localhost:8000/api/v1/gamification/badges/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 2: View My Badges:**
```bash
curl -X GET http://localhost:8000/api/v1/gamification/badges/my_badges/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 3: View My Points Summary:**
```bash
curl -X GET http://localhost:8000/api/v1/gamification/points/my_summary/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 4: View My Transaction History:**
```bash
curl -X GET http://localhost:8000/api/v1/gamification/points/my_transactions/ ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 5: View Leaderboard:**
```bash
# All-time leaderboard
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard/" ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"

# Weekly leaderboard
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard/?period=weekly" ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"

# Monthly leaderboard
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard/?period=monthly" ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

**Step 6: View My Position:**
```bash
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard/my_position/" ^
  -H "Authorization: Bearer %EMPLOYEE_TOKEN%"
```

---

## 4. Verify Signal Integration

### 4.1 Enable Django Logging

Add to `phishaware_backend/settings.py` (temporarily for debugging):

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.training.signals': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.gamification.signals': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 4.2 Test Signal: QuizResult → RiskScore Update

**Method: Django Shell**

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.companies.models import Company
from apps.campaigns.models import Campaign, Quiz, QuizResult
from apps.training.models import RiskScore

# Get test employee
alice = User.objects.get(email='alice@acme.com')
company = alice.company

# Check if RiskScore exists before
print(f"RiskScore exists before: {RiskScore.objects.filter(employee=alice).exists()}")

# Get or create a campaign
campaign = Campaign.objects.first()
if not campaign:
    campaign = Campaign.objects.create(
        name='Test Campaign',
        company=company,
        created_by=User.objects.filter(role='COMPANY_ADMIN', company=company).first(),
        num_emails=10,
        phishing_ratio=0.5,
        status='ACTIVE'
    )

# Get or create quiz
quiz, created = Quiz.objects.get_or_create(
    campaign=campaign,
    employee=alice,
    defaults={'status': 'COMPLETED'}
)

# Create QuizResult (this should trigger the signal!)
result = QuizResult.objects.create(
    quiz=quiz,
    employee=alice,
    campaign=campaign,
    total_questions=10,
    correct_answers=4,  # Low score to test remediation
    incorrect_answers=6,
    score=40,
    phishing_emails_identified=2,
    phishing_emails_missed=3,
    false_positives=1,
    risk_level='HIGH'
)

print(f"\nQuizResult created with score: {result.score}")

# Verify RiskScore was created/updated
risk_score = RiskScore.objects.get(employee=alice)
print(f"RiskScore now exists: True")
print(f"Risk Score: {risk_score.score}")
print(f"Risk Level: {risk_score.risk_level}")
print(f"Requires Remediation: {risk_score.requires_remediation}")

# Check if training was auto-assigned (if score > 70)
from apps.training.models import RemediationTraining
trainings = RemediationTraining.objects.filter(employee=alice)
print(f"Trainings assigned: {trainings.count()}")
for t in trainings:
    print(f"  - {t.training_module.title} ({t.status})")

exit()
```

### 4.3 Test Signal: TrackingEvent → RiskScore Update

```python
from apps.accounts.models import User
from apps.simulations.models import SimulationCampaign, SimulationTemplate, EmailSimulation, TrackingEvent
from apps.training.models import RiskScore
import uuid

alice = User.objects.get(email='alice@acme.com')
company = alice.company

# Get risk score before
risk_before = RiskScore.objects.get(employee=alice)
print(f"Risk Score BEFORE: {risk_before.score}")
print(f"Simulations Clicked BEFORE: {risk_before.simulations_clicked}")

# Get or create simulation campaign
template = SimulationTemplate.objects.first()
sim_campaign = SimulationCampaign.objects.first()
if not sim_campaign:
    admin = User.objects.filter(role='COMPANY_ADMIN', company=company).first()
    sim_campaign = SimulationCampaign.objects.create(
        name='Test Simulation',
        company=company,
        template=template,
        created_by=admin,
        status='IN_PROGRESS'
    )

# Get or create email simulation
email_sim, created = EmailSimulation.objects.get_or_create(
    campaign=sim_campaign,
    employee=alice,
    defaults={
        'tracking_token': uuid.uuid4(),
        'link_token': uuid.uuid4().hex[:32],
        'recipient_email': alice.email,
        'status': 'DELIVERED'
    }
)

# Create TrackingEvent for LINK_CLICKED (this triggers the signal!)
event = TrackingEvent.objects.create(
    email_simulation=email_sim,
    campaign=sim_campaign,
    employee=alice,
    event_type='LINK_CLICKED',
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0'
)

print(f"\nTrackingEvent created: {event.event_type}")

# Verify RiskScore was updated
risk_score = RiskScore.objects.get(employee=alice)
print(f"Risk Score AFTER: {risk_score.score}")
print(f"Simulations Clicked AFTER: {risk_score.simulations_clicked}")
print(f"Requires Remediation: {risk_score.requires_remediation}")

# Check auto-assigned training
from apps.training.models import RemediationTraining
trainings = RemediationTraining.objects.filter(employee=alice, assignment_reason='AUTO_SIMULATION_FAIL')
print(f"Auto-assigned trainings for simulation fail: {trainings.count()}")

exit()
```

### 4.4 Test Signal: Gamification Points & Badges

```python
from apps.accounts.models import User
from apps.gamification.models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints

alice = User.objects.get(email='alice@acme.com')

# Check points
try:
    points = EmployeePoints.objects.get(employee=alice)
    print(f"Total Points: {points.total_points}")
    print(f"Weekly Points: {points.weekly_points}")
    print(f"Badge Count: {points.badge_count}")
except EmployeePoints.DoesNotExist:
    print("No EmployeePoints record yet")

# Check badges earned
badges = EmployeeBadge.objects.filter(employee=alice)
print(f"\nBadges Earned: {badges.count()}")
for b in badges:
    print(f"  - {b.badge.name} (awarded: {b.awarded_at})")

# Check transactions
transactions = PointsTransaction.objects.filter(employee=alice).order_by('-created_at')[:10]
print(f"\nRecent Transactions:")
for t in transactions:
    print(f"  - {t.transaction_type}: {t.points} points - {t.description}")

exit()
```

### 4.5 Verify Database Records Directly

```python
from apps.training.models import RiskScore, RiskScoreHistory, RemediationTraining
from apps.gamification.models import EmployeePoints, PointsTransaction, EmployeeBadge

# Summary for all employees
from apps.accounts.models import User
from apps.companies.models import Company

company = Company.objects.get(name='Acme Corporation')
employees = User.objects.filter(company=company, role='EMPLOYEE')

print("=== Employee Status Summary ===\n")
for emp in employees:
    print(f"\n{emp.get_full_name()} ({emp.email}):")

    # Risk Score
    try:
        rs = RiskScore.objects.get(employee=emp)
        print(f"  Risk Score: {rs.score} ({rs.risk_level})")
        print(f"  Requires Remediation: {rs.requires_remediation}")
    except RiskScore.DoesNotExist:
        print(f"  Risk Score: Not calculated yet")

    # Points
    try:
        pts = EmployeePoints.objects.get(employee=emp)
        print(f"  Total Points: {pts.total_points}")
    except EmployeePoints.DoesNotExist:
        print(f"  Total Points: 0")

    # Badges
    badge_count = EmployeeBadge.objects.filter(employee=emp).count()
    print(f"  Badges: {badge_count}")

    # Trainings
    training_count = RemediationTraining.objects.filter(employee=emp).count()
    completed = RemediationTraining.objects.filter(employee=emp, status__in=['COMPLETED', 'PASSED']).count()
    print(f"  Trainings: {completed}/{training_count} completed")

exit()
```

---

## 5. End-to-End Test Workflow

This section walks through a complete employee journey to verify all integrations.

### 5.1 Setup: Ensure Clean State

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.training.models import RiskScore, RemediationTraining
from apps.gamification.models import EmployeePoints, EmployeeBadge, PointsTransaction
from apps.campaigns.models import Quiz, QuizResult

# Get Bob as our test employee
bob = User.objects.get(email='bob@acme.com')

# Clear existing data for Bob (for clean test)
RiskScore.objects.filter(employee=bob).delete()
RemediationTraining.objects.filter(employee=bob).delete()
EmployeePoints.objects.filter(employee=bob).delete()
EmployeeBadge.objects.filter(employee=bob).delete()
PointsTransaction.objects.filter(employee=bob).delete()
Quiz.objects.filter(employee=bob).delete()

print("Bob's data cleared. Ready for E2E test.")
exit()
```

### 5.2 Step 1: Employee Takes Quiz and Fails

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.companies.models import Company
from apps.campaigns.models import Campaign, Quiz, QuizResult
from apps.training.models import RiskScore

bob = User.objects.get(email='bob@acme.com')
company = bob.company
admin = User.objects.filter(role='COMPANY_ADMIN', company=company).first()

# Create campaign
campaign = Campaign.objects.create(
    name='E2E Test Campaign',
    company=company,
    created_by=admin,
    num_emails=10,
    phishing_ratio=0.5,
    status='ACTIVE'
)

# Create quiz
quiz = Quiz.objects.create(
    campaign=campaign,
    employee=bob,
    status='COMPLETED'
)

# Create QuizResult with POOR score (should trigger high risk)
result = QuizResult.objects.create(
    quiz=quiz,
    employee=bob,
    campaign=campaign,
    total_questions=10,
    correct_answers=3,  # Very low score!
    incorrect_answers=7,
    score=30,
    phishing_emails_identified=1,
    phishing_emails_missed=4,  # Missed many phishing emails
    false_positives=2,
    risk_level='HIGH'
)

print(f"QuizResult created: Score={result.score}, Risk={result.risk_level}")

# Verify risk score was created and updated
risk = RiskScore.objects.get(employee=bob)
print(f"\nRisk Score: {risk.score}")
print(f"Risk Level: {risk.risk_level}")
print(f"Requires Remediation: {risk.requires_remediation}")

# Verify points were awarded (10 points for quiz completion)
from apps.gamification.models import EmployeePoints
points = EmployeePoints.objects.get(employee=bob)
print(f"\nTotal Points: {points.total_points}")

# Verify FIRST_QUIZ_COMPLETED badge
from apps.gamification.models import EmployeeBadge
badges = EmployeeBadge.objects.filter(employee=bob)
print(f"Badges: {[b.badge.name for b in badges]}")

exit()
```

**Expected Output:**
- Risk Score > 70 (high risk due to missed phishing)
- Requires Remediation: True
- Total Points: 10 (quiz completion)
- Badge: First Quiz Champion

### 5.3 Step 2: Verify Auto-Remediation Assigned

```python
from apps.accounts.models import User
from apps.training.models import RemediationTraining

bob = User.objects.get(email='bob@acme.com')

trainings = RemediationTraining.objects.filter(employee=bob)
print(f"Trainings auto-assigned: {trainings.count()}")
for t in trainings:
    print(f"  - {t.training_module.title}")
    print(f"    Status: {t.status}")
    print(f"    Reason: {t.assignment_reason}")
    print(f"    Risk Before: {t.risk_score_before}")

exit()
```

**Expected Output:**
- At least 1 mandatory training assigned
- Reason: AUTO_HIGH_RISK
- Status: ASSIGNED

### 5.4 Step 3: Employee Completes Training

```python
from apps.accounts.models import User
from apps.training.models import RemediationTraining, TrainingQuestion
from apps.gamification.models import EmployeePoints, EmployeeBadge, PointsTransaction

bob = User.objects.get(email='bob@acme.com')

# Get first assigned training
training = RemediationTraining.objects.filter(employee=bob, status='ASSIGNED').first()

if training:
    # Start training
    training.start_training()
    print(f"Training started: {training.training_module.title}")

    # Mark content viewed
    training.mark_content_viewed()
    print("Content viewed")

    # Get questions and prepare correct answers
    questions = TrainingQuestion.objects.filter(module=training.training_module, is_active=True)
    answers = []
    for q in questions:
        answers.append({
            'question_id': q.id,
            'selected_answer_index': q.correct_answer_index  # All correct!
        })

    # Submit quiz with all correct answers
    training.submit_quiz(answers)
    print(f"\nQuiz submitted!")
    print(f"Score: {training.quiz_score}%")
    print(f"Status: {training.status}")
    print(f"Risk Score After: {training.risk_score_after}")

    # Check updated risk score
    from apps.training.models import RiskScore
    risk = RiskScore.objects.get(employee=bob)
    print(f"\nUpdated Risk Score: {risk.score}")
    print(f"Risk Level: {risk.risk_level}")

    # Check points
    points = EmployeePoints.objects.get(employee=bob)
    print(f"\nTotal Points Now: {points.total_points}")

    # Check badges
    badges = EmployeeBadge.objects.filter(employee=bob)
    print(f"Badges: {[b.badge.name for b in badges]}")
else:
    print("No assigned training found!")

exit()
```

**Expected Output:**
- Quiz Score: 100%
- Status: PASSED
- Risk Score decreased (by score_reduction_on_pass, typically 15 points)
- Points increased (15 for completion + 30 for passing + 20 for first attempt = 65 more points)
- New badge: Quick Learner (passed on first attempt)

### 5.5 Step 4: Employee Takes Another Quiz with Perfect Score

```python
from apps.accounts.models import User
from apps.campaigns.models import Campaign, Quiz, QuizResult
from apps.gamification.models import EmployeePoints, EmployeeBadge

bob = User.objects.get(email='bob@acme.com')
company = bob.company
admin = User.objects.filter(role='COMPANY_ADMIN', company=company).first()

# Create new campaign
campaign2 = Campaign.objects.create(
    name='E2E Test Campaign 2',
    company=company,
    created_by=admin,
    num_emails=10,
    phishing_ratio=0.5,
    status='ACTIVE'
)

quiz2 = Quiz.objects.create(
    campaign=campaign2,
    employee=bob,
    status='COMPLETED'
)

# Create QuizResult with PERFECT score
result2 = QuizResult.objects.create(
    quiz=quiz2,
    employee=bob,
    campaign=campaign2,
    total_questions=10,
    correct_answers=10,  # Perfect!
    incorrect_answers=0,
    score=100,
    phishing_emails_identified=5,
    phishing_emails_missed=0,
    false_positives=0,
    risk_level='LOW'
)

print(f"Perfect QuizResult created: Score={result2.score}")

# Check points (should get +10 completion + 50 perfect bonus)
points = EmployeePoints.objects.get(employee=bob)
print(f"\nTotal Points: {points.total_points}")

# Check for Perfect Score badge
badges = EmployeeBadge.objects.filter(employee=bob)
print(f"Badges: {[b.badge.name for b in badges]}")

# Check updated risk score
from apps.training.models import RiskScore
risk = RiskScore.objects.get(employee=bob)
print(f"\nRisk Score: {risk.score}")
print(f"Risk Level: {risk.risk_level}")

exit()
```

**Expected Output:**
- Points increased by 60 (10 + 50 bonus)
- New badge: Perfect Score
- Risk Score significantly lower

### 5.6 Step 5: Check Leaderboard Position

```python
from apps.accounts.models import User
from apps.gamification.models import EmployeePoints
from apps.gamification.services import get_leaderboard, get_employee_rank

bob = User.objects.get(email='bob@acme.com')
company = bob.company

# Get leaderboard
leaderboard = get_leaderboard(company_id=company.id, limit=10)
print("=== Company Leaderboard ===")
for i, entry in enumerate(leaderboard, 1):
    print(f"{i}. {entry.employee.get_full_name()} - {entry.total_points} points")

# Get Bob's rank
rank = get_employee_rank(bob)
print(f"\nBob's Rank: #{rank}")

exit()
```

### 5.7 Summary: Verify Complete Journey

```python
from apps.accounts.models import User
from apps.training.models import RiskScore, RiskScoreHistory, RemediationTraining
from apps.gamification.models import EmployeePoints, EmployeeBadge, PointsTransaction

bob = User.objects.get(email='bob@acme.com')

print("=" * 50)
print(f"E2E TEST SUMMARY FOR: {bob.get_full_name()}")
print("=" * 50)

# Risk Score Journey
print("\n--- RISK SCORE JOURNEY ---")
risk = RiskScore.objects.get(employee=bob)
print(f"Current Score: {risk.score} ({risk.risk_level})")
print(f"Quizzes Taken: {risk.total_quizzes_taken}")
print(f"Trainings Completed: {risk.trainings_completed}")

history = RiskScoreHistory.objects.filter(employee=bob).order_by('created_at')
print(f"\nHistory ({history.count()} events):")
for h in history:
    print(f"  {h.event_type}: {h.previous_score} → {h.new_score} ({h.score_change:+d})")

# Training Journey
print("\n--- TRAINING JOURNEY ---")
trainings = RemediationTraining.objects.filter(employee=bob)
print(f"Total Assigned: {trainings.count()}")
for t in trainings:
    print(f"  - {t.training_module.title}: {t.status} (Score: {t.quiz_score}%)")

# Gamification Journey
print("\n--- GAMIFICATION JOURNEY ---")
points = EmployeePoints.objects.get(employee=bob)
print(f"Total Points: {points.total_points}")
print(f"Badge Count: {points.badge_count}")

badges = EmployeeBadge.objects.filter(employee=bob)
print(f"\nBadges Earned:")
for b in badges:
    print(f"  - {b.badge.name} ({b.badge.rarity})")

transactions = PointsTransaction.objects.filter(employee=bob).order_by('created_at')
print(f"\nPoint Transactions:")
for t in transactions:
    print(f"  {t.transaction_type}: {t.points:+d} points")

print("\n" + "=" * 50)
print("E2E TEST COMPLETE!")
print("=" * 50)

exit()
```

---

## 6. Troubleshooting Guide

### 6.1 Migration Issues

**Problem: Migration fails with "relation already exists"**
```bash
# Reset migrations for specific app
python manage.py migrate app_name zero
python manage.py migrate app_name
```

**Problem: "No such table" error**
```bash
# Make sure migrations are created
python manage.py makemigrations
python manage.py migrate
```

**Problem: Circular dependency in migrations**
```bash
# Check migration order
python manage.py showmigrations --plan
```

### 6.2 Signal Issues

**Problem: Signals not firing**

1. Check signals are imported in app's `apps.py`:
```python
# apps/training/apps.py
class TrainingConfig(AppConfig):
    name = 'apps.training'

    def ready(self):
        import apps.training.signals  # Must have this!
```

2. Check app is in INSTALLED_APPS correctly:
```python
INSTALLED_APPS = [
    ...
    'apps.training',  # Not 'training'
]
```

3. Add debug logging to signal:
```python
# In signals.py
import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=QuizResult)
def update_risk_score_on_quiz(sender, instance, created, **kwargs):
    logger.debug(f"Signal fired! created={created}")
    if not created:
        return
    # ... rest of signal
```

**Problem: Signal fires multiple times**
```python
# Use dispatch_uid to prevent duplicates
@receiver(post_save, sender=QuizResult, dispatch_uid="unique_quiz_result_signal")
def update_risk_score_on_quiz(sender, instance, created, **kwargs):
    ...
```

### 6.3 API Errors

**Problem: 401 Unauthorized**
```bash
# Token might be expired, refresh it:
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ ^
  -H "Content-Type: application/json" ^
  -d "{\"refresh\": \"your_refresh_token\"}"
```

**Problem: 403 Forbidden**
- Check user role has permission
- Check if endpoint requires specific role (COMPANY_ADMIN, etc.)

**Problem: 400 Bad Request**
```bash
# Check the response body for field errors
curl -v -X POST http://localhost:8000/api/v1/... 2>&1 | findstr "error\|detail\|message"
```

**Problem: 500 Internal Server Error**
```bash
# Check Django console for traceback
# Add this to settings.py for more details:
DEBUG = True
```

### 6.4 Database Verification

**Check specific record exists:**
```python
from apps.training.models import RiskScore
from apps.accounts.models import User

user = User.objects.get(email='alice@acme.com')
try:
    risk = RiskScore.objects.get(employee=user)
    print(f"Found: {risk.score}")
except RiskScore.DoesNotExist:
    print("Not found!")
```

**Check foreign key relationships:**
```python
from apps.campaigns.models import QuizResult

result = QuizResult.objects.first()
print(f"Employee: {result.employee}")
print(f"Campaign: {result.campaign}")
print(f"Quiz: {result.quiz}")
```

**Debug signal data flow:**
```python
# Add temporary print statements in signal
@receiver(post_save, sender=QuizResult)
def update_risk_score_on_quiz(sender, instance, created, **kwargs):
    print(f"=== SIGNAL DEBUG ===")
    print(f"Created: {created}")
    print(f"Instance: {instance}")
    print(f"Employee: {instance.employee}")
    print(f"Score: {instance.score}")
    # ... rest of signal
```

### 6.5 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Risk score not updating | Signal not connected | Check `ready()` imports signal |
| Points not awarded | EmployeePoints doesn't exist | Signal should create it; check for errors |
| Badge not awarded | Badge doesn't exist in DB | Run badge creation migration or script |
| Training not auto-assigned | Score threshold not met | Score must be > 70 |
| Leaderboard empty | No EmployeePoints records | Complete at least one quiz |
| Token expired | Access token lifetime | Refresh token or re-login |

### 6.6 Useful Shell Commands

```python
# Count records per model
from apps.training.models import RiskScore, RemediationTraining
from apps.gamification.models import Badge, EmployeeBadge, PointsTransaction

print(f"RiskScores: {RiskScore.objects.count()}")
print(f"Trainings: {RemediationTraining.objects.count()}")
print(f"Badges: {Badge.objects.count()}")
print(f"EmployeeBadges: {EmployeeBadge.objects.count()}")
print(f"Transactions: {PointsTransaction.objects.count()}")
```

```python
# Find employees with high risk
from apps.training.models import RiskScore
high_risk = RiskScore.objects.filter(score__gt=70)
for r in high_risk:
    print(f"{r.employee.email}: {r.score}")
```

```python
# Find employees needing remediation
from apps.training.models import RiskScore
needing = RiskScore.objects.filter(requires_remediation=True)
print(f"Employees needing remediation: {needing.count()}")
```

---

## Quick Reference: API Endpoints

| Module | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| **Auth** | `/api/v1/auth/register/` | POST | No |
| **Auth** | `/api/v1/auth/login/` | POST | No |
| **Auth** | `/api/v1/auth/logout/` | POST | Yes |
| **Auth** | `/api/v1/auth/token/refresh/` | POST | No |
| **Auth** | `/api/v1/auth/profile/` | GET/PATCH | Yes |
| **Campaigns** | `/api/v1/campaigns/campaigns/` | GET/POST | Yes |
| **Campaigns** | `/api/v1/campaigns/quizzes/` | GET/POST | Yes |
| **Campaigns** | `/api/v1/campaigns/quizzes/{id}/submit/` | POST | Yes |
| **Simulations** | `/api/v1/simulations/templates/` | GET/POST | Yes |
| **Simulations** | `/api/v1/simulations/campaigns/` | GET/POST | Yes |
| **Simulations** | `/api/v1/simulations/track/{token}/` | GET | **No** |
| **Simulations** | `/api/v1/simulations/link/{token}/` | GET | **No** |
| **Training** | `/api/v1/training/risk-scores/my_score/` | GET | Yes |
| **Training** | `/api/v1/training/modules/` | GET | Yes |
| **Training** | `/api/v1/training/assignments/my_trainings/` | GET | Yes |
| **Training** | `/api/v1/training/assignments/{id}/submit_quiz/` | POST | Yes |
| **Gamification** | `/api/v1/gamification/badges/my_badges/` | GET | Yes |
| **Gamification** | `/api/v1/gamification/points/my_summary/` | GET | Yes |
| **Gamification** | `/api/v1/gamification/leaderboard/` | GET | Yes |

---

## Signal Flow Diagram

```
┌─────────────────┐
│   QuizResult    │
│    Created      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ training.signals│────▶│  Update Risk    │
│                 │     │     Score       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │  Score > 70?    │
         │              └────────┬────────┘
         │                       │ Yes
         │                       ▼
         │              ┌─────────────────┐
         │              │ Auto-Assign     │
         │              │   Training      │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ gamification    │────▶│  Award Points   │
│    .signals     │     │  (10 pts)       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │ Perfect Score?  │
         │              └────────┬────────┘
         │                       │ Yes
         │                       ▼
         │              ┌─────────────────┐
         │              │ Award 50 bonus  │
         │              │ + Badge         │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐
│  First Quiz?    │────▶ Award FIRST_QUIZ_COMPLETED Badge
└─────────────────┘
```

---

**End of Testing Guide**

For questions or issues, check the Django console output for error messages and stack traces.
