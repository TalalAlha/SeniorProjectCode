# PhishAware Backend

**PhishAware** is a bilingual (Arabic/English) AI-powered phishing simulation and awareness platform designed specifically for the MENA region. This repository contains the Django REST Framework backend.

## Tech Stack

- **Backend Framework**: Django 5.2+ with Django REST Framework
- **Authentication**: JWT (JSON Web Tokens) with role-based access control (RBAC)
- **Database**: SQLite (development) / PostgreSQL (production)
- **API Documentation**: Swagger/ReDoc (drf-yasg)
- **AI/ML**: PyTorch with LSTM models (trained separately)

## Features

- **Multi-role Authentication System** (Super Admin, Company Admin, Employee, Public User)
- **Interactive Quiz Campaigns** with AI-generated phishing emails
- **Live Simulation Attacks** with email tracking
- **Risk Scoring & Auto-remediation Training**
- **Gamification** (leaderboards, badges, points)
- **Public Community Awareness Portal**
- **Bilingual Support** (Arabic & English)

## Project Structure

```
Backend/
├── apps/                          # Django applications
│   ├── accounts/                  # User authentication & management
│   ├── analytics/                 # Analytics & reporting
│   ├── assessments/              # Risk scoring & training
│   ├── campaigns/                # Quiz campaigns
│   ├── community/                # Public community portal
│   ├── companies/                # Company management
│   ├── core/                     # Core utilities & permissions
│   ├── gamification/             # Gamification features
│   └── simulations/              # Live simulation attacks
├── phishaware_backend/           # Django project settings
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- pip (Python package manager)
- Virtual environment (recommended)

### 2. Installation

Clone the repository and navigate to the Backend directory:

```bash
cd Backend
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Database Setup

Run migrations to create database tables:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to set up your admin account.

### 5. Run Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login (get JWT tokens)
- `POST /api/v1/auth/logout/` - Logout (blacklist refresh token)
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `GET /api/v1/auth/profile/` - Get user profile
- `PATCH /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/change-password/` - Change password

### Campaigns & Quizzes

- `POST /api/v1/campaigns/campaigns/` - Create campaign
- `GET /api/v1/campaigns/campaigns/` - List campaigns
- `GET /api/v1/campaigns/campaigns/{id}/` - Get campaign details
- `PATCH /api/v1/campaigns/campaigns/{id}/` - Update campaign
- `POST /api/v1/campaigns/campaigns/{id}/activate/` - Activate campaign
- `POST /api/v1/campaigns/campaigns/{id}/assign_to_employees/` - Assign to employees
- `GET /api/v1/campaigns/campaigns/{id}/statistics/` - Get campaign statistics
- `GET /api/v1/campaigns/quizzes/` - List quizzes (employee's own or all for admin)
- `POST /api/v1/campaigns/quizzes/{id}/start/` - Start quiz
- `GET /api/v1/campaigns/quizzes/{id}/questions/` - Get quiz questions
- `POST /api/v1/campaigns/quizzes/{id}/answer_question/` - Answer question
- `POST /api/v1/campaigns/quizzes/{id}/submit/` - Submit quiz
- `GET /api/v1/campaigns/quizzes/{id}/result/` - Get quiz results

### Email Templates & AI

- `GET /api/v1/assessments/email-templates/` - List email templates
- `POST /api/v1/assessments/email-templates/` - Create email template
- `POST /api/v1/assessments/ai/generate-emails/` - Generate emails with AI

For detailed campaign workflow documentation, see [CAMPAIGNS.md](CAMPAIGNS.md)

### Admin Panel

Access the Django admin panel at: `http://localhost:8000/admin`

### API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

## User Roles

The platform supports four user roles with different permissions:

1. **Super Admin** - Platform administrators with full access
2. **Company Admin** - Company administrators who manage their organization
3. **Employee** - Company employees who participate in training
4. **Public User** - Public users accessing community resources

## RBAC Permissions

Custom permission classes in `apps/core/permissions.py`:

- `IsSuperAdmin` - Only super admins
- `IsCompanyAdmin` - Only company admins
- `IsEmployee` - Only employees
- `IsPublicUser` - Only public users
- `IsSuperAdminOrCompanyAdmin` - Super admins or company admins
- `HasCompanyAccess` - Users with company access
- `IsSameCompany` - Users from the same company
- `IsOwnerOrAdmin` - Object owner or admin

## Development Workflow

### Creating Migrations

After modifying models:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Tests

```bash
python manage.py test
```

### Static Files Collection (Production)

```bash
python manage.py collectstatic
```

## Database Models

### User Model (`accounts.User`)

Custom user model with email-based authentication and role-based access control.

**Key Fields:**
- email (unique)
- first_name, last_name
- role (SUPER_ADMIN, COMPANY_ADMIN, EMPLOYEE, PUBLIC_USER)
- company (ForeignKey to Company)
- preferred_language (en/ar)

### Company Model (`companies.Company`)

Organization model for managing companies using the platform.

**Key Fields:**
- name (unique)
- industry, company_size
- country, city
- subscription dates
- is_active

## Production Deployment

For production deployment with PostgreSQL:

1. Install PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `.env` with PostgreSQL credentials:
   ```env
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=phishaware_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. Update `settings.py` to use PostgreSQL configuration

4. Set `DEBUG=False` and configure proper `ALLOWED_HOSTS`

## Contributing

This is a senior project for educational purposes. For questions or issues, please contact the development team.

## License

MIT License - See LICENSE file for details

## Contact

For support or inquiries, contact: support@phishaware.com
