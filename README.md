# 🛡️ PhishAware - Phishing Awareness Training Platform

A comprehensive security awareness training platform designed for organizations in the MENA region to combat phishing threats through interactive campaigns, simulations, and gamified learning.

## 📋 Table of Contents

- [Overview](#Overview)
- [Features](#Features)
- [Tech Stack](#Tech-Stack)
- [Project Structure](#Project-Structure)
- [Installation](#Installation)



---

## 🎯 Overview

PhishAware is a multi-tenant SaaS platform that helps organizations train their employees to identify and respond to phishing attacks. The platform combines educational campaigns, real-world simulations, risk scoring, and gamification to create an engaging and effective security awareness program.

**Target Region:** MENA (Middle East & North Africa)  
**Languages:** English & Arabic (bilingual support with RTL)  
**Architecture:** Full-stack web application with RESTful API

---

## ✨ Features

### 🎓 Interactive Quiz Campaigns
- Create educational campaigns with customizable email counts and phishing ratios
- AI-powered phishing email generation 
- Assign campaigns to employees or groups
- Track completion rates and scores
- Automated quiz result processing

### 🎣 Live Phishing Simulations
- Create realistic phishing simulation campaigns
- Template-based email generation
- Unique tracking links per employee
- Download CSV packages for manual email sending
- Track opens, clicks, and reports
- Real-time analytics dashboard

### 📊 Risk Scoring & Auto-Remediation
- Dynamic risk scoring algorithm (0-100 scale)
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Automatic training assignment for high-risk employees
- Risk score history tracking
- Signal-based auto-updates

### 🎮 Gamification System
- Badge system (6+ achievement badges)
- Points for completing activities
- Weekly, monthly, and all-time leaderboards
- Automatic badge awards via Django signals
- Progress tracking

### 👥 Company & User Management
- Multi-tenant architecture
- Bulk employee invitations
- CSV import for employee data
- Role-based access control (RBAC)
- Company-wide statistics

### 📈 Analytics & Reporting
- Real-time dashboards with charts (Recharts)
- Campaign performance metrics
- Simulation effectiveness tracking
- Risk distribution analytics
- Training completion rates
- CSV export functionality

### 🌐 Community Awareness Portal
- Public articles and blog posts (no auth required)
- Public quizzes for general awareness
- Resource library (PDFs, videos, links)
- Bilingual content (EN/AR)
- SEO-friendly URLs

### 📚 Training Management
- Training modules with content and quizzes
- Automatic assignment based on risk scores
- Progress tracking
- Quiz-based assessments

---

## 🛠️ Tech Stack

### Backend
- **Framework:** Django 5.2.10
- **API:** Django REST Framework 3.16.1
- **Authentication:** JWT (djangorestframework-simplejwt 5.5.1)
- **Database:** SQLite (dev) / PostgreSQL (production)
- **AI Model:** PyTorch LSTM (for email generation)
- **Python:** 3.14.2

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **Charts:** Recharts
- **Icons:** Lucide React
- **Notifications:** React Hot Toast
- **i18n:** react-i18next (bilingual EN/AR)


---

## 📁 Project Structure
```
PhishAware/
├── Backend/                    # Django backend
│   ├── apps/
│   │   ├── accounts/          # Authentication & users
│   │   ├── campaigns/         # Quiz campaigns
│   │   ├── simulations/       # Phishing simulations
│   │   ├── training/          # Training modules & risk scoring
│   │   ├── gamification/      # Badges, points, leaderboards
│   │   ├── companies/         # Company management
│   │   ├── analytics/         # Analytics & reporting
│   │   └── community/         # Public portal
│   ├── phishaware_backend/    # Project settings
│   ├── manage.py
│   ├── requirements.txt
│   └── venv/
│
└── Frontend/                   # React frontend (Later)

```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- npm or yarn
- Git

### Backend Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/phishaware.git
cd phishaware/Backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Create superuser:**
```bash
python manage.py createsuperuser
```

6. **Run development server:**
```bash
python manage.py runserver
```

Backend runs at: `http://localhost:8000`
