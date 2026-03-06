# PhishAware — Backend

Django REST Framework API powering the PhishAware cybersecurity awareness platform.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.x + Django REST Framework 3.x |
| Authentication | SimpleJWT (JWT access + refresh tokens, token blacklisting) |
| Database | SQLite (development) / PostgreSQL (production) |
| Email | SendGrid via SMTP relay (`django.core.mail`) |
| API Docs | drf-yasg (Swagger + ReDoc) |
| Environment | python-decouple (`.env` file) |
| CORS | django-cors-headers |

---

## Project Structure

```
Backend/
├── apps/
│   ├── accounts/       # Auth, registration, email verification, invitations, password reset
│   ├── companies/      # Company CRUD, user management, CSV import
│   ├── campaigns/      # Assessment campaigns: email classification quizzes, scoring, results
│   ├── simulations/    # Live phishing simulations: email dispatch, click/report tracking
│   ├── training/       # Training modules, quizzes, risk scores, remediation assignments
│   ├── analytics/      # Dashboard stats, trends, risk analytics, CSV export
│   ├── notifications/  # 36-type notification system
│   ├── gamification/   # Badges and leaderboard
│   ├── community/      # Community portal
│   └── core/           # Shared permissions, email helpers, HTML email templates
├── phishaware_backend/
│   ├── settings.py
│   └── urls.py
├── requirements.txt
└── manage.py
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the `Backend/` directory:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173

# Email — SendGrid SMTP relay
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=PhishAware <no-reply@yourdomain.com>
SENDGRID_VERIFIED_SENDER=no-reply@yourdomain.com
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Seed initial data

```bash
# 15 global phishing simulation templates (8 English + 7 Arabic)
python manage.py seed_simulation_templates

# 3 training modules with 5 bilingual quiz questions each
python manage.py seed_training
```

### 6. Create a Super Admin account

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

API available at: `http://localhost:8000/api/v1/`

---

## API Reference

### Authentication — `/api/v1/auth/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register/` | Register new user | Public |
| POST | `/login/` | Obtain JWT tokens | Public |
| POST | `/logout/` | Blacklist refresh token | Required |
| POST | `/token/refresh/` | Refresh access token | Public |
| POST | `/verify-email/<uuid>/` | Confirm email address | Public |
| POST | `/resend-verification/` | Resend verification email | Public |
| POST | `/password-reset/` | Request password reset link | Public |
| POST | `/password-reset/<uuid>/` | Set new password via token | Public |
| GET/PATCH | `/profile/` | Get or update user profile | Required |
| POST | `/change-password/` | Change password | Required |

### Employee Invitations — `/api/v1/employees/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/invite/` | Send invitation email | Admin |
| GET | `/invite/<uuid>/` | Get invitation details | Public |
| POST | `/invite/<uuid>/accept/` | Accept invitation, set password | Public |
| GET | `/pending/` | List pending invitations | Admin |
| POST | `/<id>/resend/` | Resend invitation (rotates token) | Admin |
| DELETE | `/<id>/cancel/` | Cancel invitation | Admin |

### Companies — `/api/v1/companies/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register/` | Self-service company registration | Public |
| GET | `/` | List companies | Required |
| GET/PATCH | `/<id>/` | Company detail / update | Required |
| POST | `/<id>/activate/` | Activate company | Super Admin |
| POST | `/<id>/deactivate/` | Deactivate company | Super Admin |
| GET | `/<id>/stats/` | Company statistics | Admin |
| GET | `/<id>/users/` | List company users | Admin |
| DELETE | `/<id>/users/<uid>/remove/` | Remove user from company | Admin |
| POST | `/<id>/import_csv/` | Bulk import users from CSV | Admin |
| GET | `/my_company/` | Get own company | Required |

### Campaigns — `/api/v1/campaigns/`

Assessment-style exercises where employees classify a set of emails (phishing or legitimate) through a quiz interface. Different from Simulations — no real emails are sent; employees take a quiz to test their awareness.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET/POST | `/campaigns/` | List / create campaigns | Admin |
| GET/PATCH | `/campaigns/<id>/` | Campaign detail / update | Admin |
| DELETE | `/campaigns/<id>/` | Delete campaign | Admin |
| POST | `/campaigns/<id>/activate/` | Activate campaign | Admin |
| POST | `/campaigns/<id>/assign_to_employees/` | Assign to employees (creates quizzes) | Admin |
| GET | `/campaigns/<id>/statistics/` | Completion rate, avg score, risk distribution | Admin |
| GET | `/campaigns/<id>/assigned_employees/` | List employees with quiz status and score | Admin |
| GET | `/quizzes/` | List quizzes (own for employees, all for admins) | Required |
| GET | `/quizzes/<id>/questions/` | Get quiz questions (no answers revealed) | Required |
| POST | `/quizzes/<id>/start/` | Start quiz | Employee |
| POST | `/quizzes/<id>/answer_question/` | Submit answer for a single question | Employee |
| POST | `/quizzes/<id>/submit/` | Finalize quiz and calculate result | Employee |
| GET | `/quizzes/<id>/result/` | View result with per-question breakdown | Required |

---

### Simulations — `/api/v1/simulations/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET/POST | `/templates/` | List / create templates | Required |
| GET/PATCH | `/templates/<id>/` | Template detail / update | Required |
| GET/POST | `/campaigns/` | List / create campaigns | Required |
| GET/PATCH | `/campaigns/<id>/` | Campaign detail / update | Required |
| POST | `/campaigns/<id>/send/` | Dispatch simulation emails | Admin |
| GET | `/link/<token>/` | Track link click (phishing lure) | **Public** |
| POST | `/report/<token>/` | Employee reports phishing email | **Public** |
| POST | `/credentials/<token>/` | Log credential submission | **Public** |
| GET | `/feedback/<token>/` | Get educational feedback | **Public** |

### Training — `/api/v1/training/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/risk-scores/` | List risk scores (role-filtered) | Required |
| GET | `/risk-scores/my_score/` | Own risk score | Required |
| GET | `/risk-scores/statistics/` | Company-wide statistics | Admin |
| GET | `/risk-scores/<id>/history/` | Score change history | Required |
| GET/POST | `/modules/` | List / create training modules | Required |
| GET | `/modules/<id>/questions/` | Get module quiz questions | Required |
| GET/POST | `/assignments/` | List / create assignments | Required |
| POST | `/assignments/<id>/start/` | Start training | Required |
| POST | `/assignments/<id>/view_content/` | Mark content viewed | Required |
| GET | `/assignments/<id>/quiz/` | Get quiz questions | Required |
| POST | `/assignments/<id>/submit_quiz/` | Submit quiz answers | Required |
| POST | `/assignments/bulk_assign/` | Bulk assign training | Admin |
| GET | `/assignments/my_trainings/` | Own assignments | Required |
| GET | `/assignments/overdue/` | Overdue assignments | Admin |

### Analytics — `/api/v1/analytics/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/dashboard/overview/` | Platform/company overview stats | Required |
| GET | `/dashboard/trends/` | Time-series data (`?period=7d\|30d\|90d`) | Required |
| GET | `/campaigns/<id>/` | Detailed campaign analytics | Required |
| GET | `/risk/distribution/` | Risk score distribution | Required |
| GET | `/risk/trends/` | Risk score trends over time | Required |
| GET | `/risk/high_risk_employees/` | High-risk employee list | Admin |
| GET | `/training/` | Training summary | Required |
| GET | `/training/effectiveness/` | Training impact analysis | Required |
| POST | `/export/csv/` | Export data to CSV | Required |

### Notifications — `/api/v1/notifications/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | List own notifications | Required |
| GET | `/unread_count/` | Unread notification count | Required |
| POST | `/<id>/mark_read/` | Mark single notification as read | Required |
| POST | `/mark_all_read/` | Mark all as read | Required |
| DELETE | `/clear_all/` | Delete all notifications | Required |

---

## User Roles

| Role | Permissions |
|------|-------------|
| `SUPER_ADMIN` | Full access across all companies and global data |
| `COMPANY_ADMIN` | Full access within own company only |
| `EMPLOYEE` | Read-only access to own data (training, score, profile) |

---

## Key Design Decisions

**JWT Authentication** — Access tokens are short-lived. Refresh tokens are blacklisted on logout. Unverified users (`is_verified=False`) cannot obtain tokens. Staff accounts (`is_staff=True`) bypass the verification check for admin convenience.

**Invitation-Only Employees** — Employees cannot self-register. A Company Admin sends a time-limited (7-day) UUID invitation token via email. On acceptance the account activates immediately, with `is_verified=True` set automatically — no separate email verification needed.

**Denormalized Campaign Statistics** — `SimulationCampaign` caches `total_sent`, `total_opened`, `total_clicked`, `total_reported` directly on the model for instant reads. Updated atomically every time a `TrackingEvent` is saved via `_update_simulation_stats()` and `_update_campaign_stats()`.

**Risk Score Signals** — Employee risk scores recalculate automatically via a Django `post_save` signal on `TrackingEvent` (`training/signals.py`). The signal fires after `super().save()`, before the inline stat methods.

**Non-Blocking Email** — All email dispatch is wrapped in try/except. Failures are logged (`logger.error`) but never raised to the API caller, preventing email infrastructure issues from breaking registration or invitation flows.

---

## Email Templates

Five branded HTML templates live in `apps/core/templates/emails/`:

| Template File | Trigger |
|---------------|---------|
| `verification.html` | User registration |
| `invitation.html` | Employee invited by admin |
| `password_reset.html` | Password reset request |
| Company welcome (inline) | Company Admin verifies email |
| Password changed (inline) | Password change confirmation |

**Test email delivery:**

```bash
python manage.py test_email --to your@email.com --type all
# --type options: all | verification | invitation | password_reset
```

---

## Seeded Data

| Command | What it creates |
|---------|----------------|
| `seed_simulation_templates` | 15 phishing templates: 8 English + 7 Arabic, covering link manipulation, credential harvesting, urgency scams, authority impersonation, and business email compromise |
| `seed_training` | 3 modules — Email Security, Mobile Security, Social Engineering — each with 5 bilingual (EN/AR) quiz questions |

---

## Notification Types (36 total)

The notification system covers all significant platform events:

- **Employee — Training (7):** assigned, due soon, due tomorrow, overdue, completed, quiz passed, quiz failed
- **Employee — Simulation (4):** link clicked, email reported, campaign launched, expired safe
- **Employee — Account (5):** welcome, profile updated, password changed, score up, score down
- **Admin — Employee Actions (6):** employee clicked, reported, training completed, failed quiz, multiple failures, high risk
- **Admin — Campaign (5):** campaign completed, progress update, high click rate, low report rate, emails sent
- **Admin — Training (3):** deadline approaching, overdue alert, monthly report ready
- **Admin — Staff (2):** employee joined, invitation expired
- **Super Admin (3):** new company registered, system alert, backup completed

---

## API Documentation (Development)

- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`
