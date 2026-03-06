# PhishAware Backend Architecture

## Overview

PhishAware backend is built using Django and Django REST Framework, following a modular architecture with separate apps for different functionalities.

## Application Structure

### Core Apps

#### 1. **accounts** - User Authentication & Management
- **Purpose**: Handle user authentication, registration, and profile management
- **Models**: User (custom user model with email authentication)
- **Key Features**:
  - JWT-based authentication
  - Role-based access control (RBAC)
  - User profile management
  - Password change functionality
  - Token blacklisting for logout

#### 2. **companies** - Company Management
- **Purpose**: Manage organizations using the platform
- **Models**: Company
- **Key Features**:
  - Company registration and profile
  - Subscription management
  - Multi-language support (English/Arabic)
  - Industry and company size tracking

#### 3. **campaigns** - Quiz Campaigns
- **Purpose**: Interactive phishing awareness quiz campaigns
- **Models**: (To be implemented)
  - Campaign
  - Question
  - Response
- **Key Features**:
  - AI-generated phishing email scenarios
  - Quiz creation and management
  - Results tracking

#### 4. **simulations** - Live Simulation Attacks
- **Purpose**: Real-world phishing simulation attacks
- **Models**: (To be implemented)
  - Simulation
  - SimulationTarget
  - SimulationResult
- **Key Features**:
  - Email simulation attacks
  - Click tracking
  - User response monitoring

#### 5. **assessments** - Email Templates & Quiz Content
- **Purpose**: Manage email templates and quiz content for campaigns
- **Models**:
  - EmailTemplate (phishing/legitimate email content)
  - QuizQuestion (links templates to quizzes)
- **Key Features**:
  - Bilingual email templates (EN/AR)
  - AI-generated content support
  - Red flags documentation
  - Difficulty levels

#### 5b. **training** - Risk Scoring & Remediation Engine
- **Purpose**: Calculate employee risk levels and manage remediation training
- **Models**:
  - RiskScore (current risk level per employee)
  - RiskScoreHistory (track score changes over time)
  - TrainingModule (training content library)
  - TrainingQuestion (quiz questions for modules)
  - RemediationTraining (assigned training records)
  - TrainingQuizAnswer (individual quiz answers)
- **Key Features**:
  - Risk score calculation (0-100 scale)
  - Risk levels: LOW (0-30), MEDIUM (31-60), HIGH (61-80), CRITICAL (81-100)
  - Auto-remediation: Assigns training when score > 70
  - Training content library with bilingual support
  - Post-training quiz system
  - Score reduction on training completion
  - Full audit trail via RiskScoreHistory
- **Signals**:
  - QuizResult.save() → Updates RiskScore with quiz statistics
  - TrackingEvent.save() → Updates RiskScore from simulations
  - RiskScore.save() (if > 70) → Auto-assigns RemediationTraining
- **API Endpoints**:
  - GET /api/v1/training/risk-scores/ - List risk scores
  - GET /api/v1/training/risk-scores/my_score/ - Employee's own score
  - GET /api/v1/training/risk-scores/statistics/ - Company statistics
  - POST /api/v1/training/risk-scores/recalculate/ - Recalculate scores
  - GET /api/v1/training/modules/ - List training modules
  - POST /api/v1/training/assignments/ - Assign training
  - POST /api/v1/training/assignments/bulk_assign/ - Bulk assign
  - POST /api/v1/training/assignments/{id}/start/ - Start training
  - POST /api/v1/training/assignments/{id}/submit_quiz/ - Submit quiz

#### 6. **gamification** - Gamification & Rewards
- **Purpose**: Gamification features to engage users
- **Models**: (To be implemented)
  - Badge
  - Leaderboard
  - Achievement
- **Key Features**:
  - Points system
  - Badges and achievements
  - Company-wide leaderboards

#### 7. **community** - Public Community Portal
- **Purpose**: Public awareness and educational content
- **Models**: (To be implemented)
  - Article
  - Resource
  - Comment
- **Key Features**:
  - Educational articles
  - Security tips
  - Community discussions

#### 8. **analytics** - Analytics & Reporting
- **Purpose**: Data analytics and reporting dashboards
- **Models**: (To be implemented)
  - Report
  - Metric
  - Insight
- **Key Features**:
  - Campaign analytics
  - Company performance metrics
  - User behavior insights

#### 9. **core** - Core Utilities
- **Purpose**: Shared utilities and base classes
- **Components**:
  - RBAC permission classes
  - Base models
  - Utility functions
  - Custom middleware

## Authentication & Authorization

### User Roles

```
┌─────────────────┐
│  SUPER_ADMIN    │  Platform-wide administration
└─────────────────┘
        │
        ├── Manage all companies
        ├── System configuration
        └── Full access to all features

┌─────────────────┐
│ COMPANY_ADMIN   │  Company-level administration
└─────────────────┘
        │
        ├── Manage company users
        ├── Create campaigns
        ├── View company analytics
        └── Configure company settings

┌─────────────────┐
│    EMPLOYEE     │  Company employee
└─────────────────┘
        │
        ├── Participate in campaigns
        ├── View personal scores
        ├── Access training materials
        └── View company leaderboard

┌─────────────────┐
│  PUBLIC_USER    │  Public community member
└─────────────────┘
        │
        ├── Access community portal
        ├── Read articles
        └── View public resources
```

### Permission Classes

Located in `apps/core/permissions.py`:

- `IsSuperAdmin` - Super admin only
- `IsCompanyAdmin` - Company admin only
- `IsEmployee` - Employee only
- `IsPublicUser` - Public user only
- `IsSuperAdminOrCompanyAdmin` - Admin access
- `HasCompanyAccess` - Company members only
- `IsSameCompany` - Same company validation
- `IsOwnerOrAdmin` - Owner or admin access

### JWT Token Flow

```
1. Login
   POST /api/v1/auth/login/
   → Returns: access_token, refresh_token, user_data

2. Access Protected Endpoints
   Headers: Authorization: Bearer <access_token>

3. Refresh Token
   POST /api/v1/auth/token/refresh/
   Body: { refresh: <refresh_token> }
   → Returns: new access_token

4. Logout
   POST /api/v1/auth/logout/
   Body: { refresh_token: <refresh_token> }
   → Blacklists the refresh token
```

## Database Schema

### User Model (accounts.User)

```python
User
├── id (BigAutoField, PK)
├── email (EmailField, unique)
├── password (CharField, hashed)
├── first_name (CharField)
├── last_name (CharField)
├── phone_number (CharField)
├── role (CharField, choices)
├── company_id (ForeignKey → Company)
├── preferred_language (CharField)
├── is_active (BooleanField)
├── is_staff (BooleanField)
├── is_verified (BooleanField)
├── date_joined (DateTimeField)
├── last_login (DateTimeField)
└── updated_at (DateTimeField)
```

### Company Model (companies.Company)

```python
Company
├── id (BigAutoField, PK)
├── name (CharField, unique)
├── name_ar (CharField)
├── description (TextField)
├── description_ar (TextField)
├── email (EmailField)
├── phone (CharField)
├── website (URLField)
├── country (CharField)
├── city (CharField)
├── address (TextField)
├── industry (CharField, choices)
├── company_size (CharField, choices)
├── is_active (BooleanField)
├── subscription_start_date (DateField)
├── subscription_end_date (DateField)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)
```

## API Structure

```
/api/v1/
├── auth/                      # Authentication endpoints
│   ├── register/             # POST - User registration
│   ├── login/                # POST - User login
│   ├── logout/               # POST - User logout
│   ├── token/refresh/        # POST - Refresh access token
│   ├── profile/              # GET, PATCH - User profile
│   └── change-password/      # POST - Change password
│
├── companies/                # (To be implemented)
├── campaigns/                # (To be implemented)
├── simulations/              # (To be implemented)
├── assessments/              # (To be implemented)
├── gamification/             # (To be implemented)
├── community/                # (To be implemented)
└── analytics/                # (To be implemented)
```

## Settings Configuration

### Key Settings

- **Authentication**: JWT with SimpleJWT
- **CORS**: Configured for React frontend
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Internationalization**: English (en) and Arabic (ar)
- **Timezone**: Asia/Dubai (MENA region)
- **Static Files**: Configured for production deployment
- **Media Files**: For user uploads and generated content

### Environment Variables

Managed via `python-decouple` in `.env` file:
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- CORS_ALLOWED_ORIGINS
- Database credentials (production)
- Email configuration

## Security Features

1. **JWT Authentication**
   - Short-lived access tokens (1 hour)
   - Long-lived refresh tokens (7 days)
   - Token rotation and blacklisting

2. **RBAC (Role-Based Access Control)**
   - Four distinct user roles
   - Granular permission classes
   - Object-level permissions

3. **Password Security**
   - Django's built-in password validators
   - Secure password hashing (PBKDF2)
   - Password change functionality

4. **CORS Protection**
   - Configured allowed origins
   - Credential support for cookies
   - Secure headers

5. **Production Security**
   - HTTPS enforcement
   - Secure cookies
   - XSS protection
   - Content type sniffing prevention

## Development Workflow

1. **Adding New Features**
   ```bash
   # Create models in appropriate app
   # Create serializers
   # Create views/viewsets
   # Add URLs
   # Create tests
   python manage.py makemigrations
   python manage.py migrate
   python manage.py test
   ```

2. **API Documentation**
   - Automatically generated via drf-yasg
   - Access at `/api/docs/` (Swagger UI)
   - Access at `/api/redoc/` (ReDoc)

## Next Steps for Implementation

1. **Companies App**
   - Company CRUD endpoints
   - Company user management
   - Subscription management

2. **Campaigns App**
   - Campaign creation and management
   - AI integration for email generation
   - Quiz question management
   - Results tracking

3. **Simulations App**
   - Simulation campaign creation
   - Email sending integration
   - Click tracking system
   - Result collection

4. **Assessments App**
   - Risk scoring algorithm
   - Training module creation
   - Auto-assignment logic
   - Progress tracking

5. **Gamification App**
   - Points calculation system
   - Badge/achievement system
   - Leaderboard generation
   - Notifications

6. **Community App**
   - Article management
   - Resource library
   - Comment system
   - Moderation tools

7. **Analytics App**
   - Dashboard endpoints
   - Report generation
   - Data visualization
   - Export functionality

## Technology Choices

### Why Django?
- Mature, secure framework
- Built-in admin panel
- ORM for database abstraction
- Extensive ecosystem

### Why Django REST Framework?
- Powerful serialization
- Built-in authentication
- Browsable API
- Extensive documentation

### Why JWT?
- Stateless authentication
- Scalable architecture
- Mobile app friendly
- Token-based security

### Why SQLite → PostgreSQL?
- Easy development setup (SQLite)
- Production-ready scalability (PostgreSQL)
- Django supports both seamlessly

## Deployment Considerations

1. **Environment Separation**
   - Development (SQLite, DEBUG=True)
   - Staging (PostgreSQL, DEBUG=True)
   - Production (PostgreSQL, DEBUG=False)

2. **Scaling Strategy**
   - Horizontal scaling with load balancers
   - Database connection pooling
   - Redis for caching
   - Celery for async tasks

3. **Monitoring**
   - Application logging
   - Error tracking (Sentry)
   - Performance monitoring
   - Database query optimization
