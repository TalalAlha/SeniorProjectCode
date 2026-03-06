# Campaign & Quiz System Documentation

## Overview

The Campaign & Quiz System is the core feature of PhishAware, allowing company admins to create phishing awareness campaigns and employees to participate in interactive quizzes.

## Workflow

```
1. Admin creates campaign
   ↓
2. Admin generates AI emails (or creates manually)
   ↓
3. Admin activates campaign
   ↓
4. Admin assigns campaign to employees
   ↓
5. Employees take quizzes
   ↓
6. System calculates results and risk scores
   ↓
7. Admins view analytics and assign training
```

## API Endpoints

### Campaign Management

#### 1. Create Campaign

```http
POST /api/v1/campaigns/campaigns/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Q1 2024 Phishing Awareness",
  "name_ar": "التوعية بالتصيد الاحتيالي - الربع الأول 2024",
  "description": "Quarterly phishing awareness campaign for all employees",
  "description_ar": "حملة التوعية الفصلية للتصيد الاحتيالي لجميع الموظفين",
  "company": 1,
  "num_emails": 10,
  "phishing_ratio": 0.5,
  "status": "DRAFT",
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-28T23:59:59Z"
}
```

**Response:** Campaign object with ID

#### 2. List Campaigns

```http
GET /api/v1/campaigns/campaigns/
Authorization: Bearer <access_token>
```

**Response:** List of campaigns for user's company

#### 3. Get Campaign Details

```http
GET /api/v1/campaigns/campaigns/{id}/
Authorization: Bearer <access_token>
```

**Response:** Detailed campaign information

#### 4. Update Campaign

```http
PATCH /api/v1/campaigns/campaigns/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "SCHEDULED",
  "start_date": "2024-02-05T00:00:00Z"
}
```

#### 5. Delete Campaign

```http
DELETE /api/v1/campaigns/campaigns/{id}/
Authorization: Bearer <access_token>
```

### Email Generation

#### Generate AI Emails

```http
POST /api/v1/assessments/ai/generate-emails/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "campaign_id": 1,
  "num_phishing_emails": 5,
  "num_legitimate_emails": 5,
  "language": "en",
  "difficulty_distribution": {
    "EASY": 2,
    "MEDIUM": 2,
    "HARD": 1
  }
}
```

**Response:**
```json
{
  "message": "Emails generated successfully",
  "campaign_id": 1,
  "generated_count": {
    "phishing": 5,
    "legitimate": 5,
    "total": 10
  },
  "emails": {
    "phishing_emails": [...],
    "legitimate_emails": [...]
  }
}
```

**Note:** The AI generation endpoint currently uses sample templates. In production, this should be integrated with your PyTorch LSTM model.

### Email Template Management

#### List Email Templates

```http
GET /api/v1/assessments/email-templates/
Authorization: Bearer <access_token>
```

#### Create Manual Email Template

```http
POST /api/v1/assessments/email-templates/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "campaign": 1,
  "sender_name": "IT Support",
  "sender_email": "support@fake-company.com",
  "subject": "Password Reset Required",
  "body": "Your password will expire soon...",
  "email_type": "PHISHING",
  "category": "CREDENTIAL_HARVESTING",
  "difficulty": "MEDIUM",
  "red_flags": [
    "Suspicious domain",
    "Urgency tactics",
    "Generic greeting"
  ],
  "explanation": "This email shows classic phishing indicators...",
  "language": "en"
}
```

### Campaign Activation & Assignment

#### Activate Campaign

```http
POST /api/v1/campaigns/campaigns/{id}/activate/
Authorization: Bearer <access_token>
```

**Prerequisites:**
- Campaign must have at least `num_emails` email templates
- Campaign status cannot already be 'ACTIVE'

#### Assign Campaign to Employees

```http
POST /api/v1/campaigns/campaigns/{id}/assign_to_employees/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "employee_ids": [5, 6, 7, 8, 9]
}
```

**Response:**
```json
{
  "created_quizzes": [...],
  "errors": [],
  "total_created": 5
}
```

**What happens:**
- Creates a Quiz instance for each employee
- Randomly selects and shuffles emails from the campaign pool
- Creates QuizQuestion instances linking emails to the quiz

### Quiz Taking (Employee Flow)

#### 1. Get My Quizzes

```http
GET /api/v1/campaigns/quizzes/
Authorization: Bearer <access_token>
```

**Response:** List of quizzes assigned to the authenticated employee

#### 2. Get Quiz Details

```http
GET /api/v1/campaigns/quizzes/{quiz_id}/
Authorization: Bearer <access_token>
```

#### 3. Get Quiz Questions

```http
GET /api/v1/campaigns/quizzes/{quiz_id}/questions/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "quiz_id": 1,
  "campaign_name": "Q1 2024 Phishing Awareness",
  "status": "NOT_STARTED",
  "total_questions": 10,
  "current_question_index": 0,
  "questions": [
    {
      "id": 1,
      "question_number": 1,
      "email_subject": "Password Reset Required",
      "email_sender_name": "IT Support",
      "email_sender_email": "support@company.com",
      "email_body": "Your password will expire...",
      "has_attachments": false,
      "attachment_names": [],
      "links": ["http://fake-link.com"],
      "answer": null,
      "confidence_level": null
    },
    ...
  ]
}
```

#### 4. Start Quiz

```http
POST /api/v1/campaigns/quizzes/{quiz_id}/start/
Authorization: Bearer <access_token>
```

**Effect:** Sets status to 'IN_PROGRESS' and records start time

#### 5. Answer Question

```http
POST /api/v1/campaigns/quizzes/{quiz_id}/answer_question/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question_number": 1,
  "answer": "PHISHING",
  "confidence_level": 4,
  "time_spent_seconds": 45
}
```

**Response:**
```json
{
  "message": "Answer submitted successfully",
  "question_number": 1,
  "quiz_progress": 10.0
}
```

**Valid answers:** `"PHISHING"` or `"LEGITIMATE"`

#### 6. Submit Quiz

```http
POST /api/v1/campaigns/quizzes/{quiz_id}/submit/
Authorization: Bearer <access_token>
```

**Prerequisites:**
- All questions must be answered
- Quiz cannot already be completed

**Response:**
```json
{
  "message": "Quiz submitted successfully",
  "result": {
    "id": 1,
    "employee_name": "John Doe",
    "campaign_name": "Q1 2024 Phishing Awareness",
    "total_questions": 10,
    "correct_answers": 8,
    "incorrect_answers": 2,
    "score": 80.0,
    "accuracy": 80.0,
    "phishing_emails_identified": 4,
    "phishing_emails_missed": 1,
    "false_positives": 1,
    "phishing_detection_rate": 80.0,
    "time_taken_seconds": 450,
    "average_time_per_question": 45.0,
    "risk_level": "MEDIUM",
    "passed": true,
    "completed_at": "2024-01-31T12:00:00Z"
  }
}
```

#### 7. View Quiz Results

```http
GET /api/v1/campaigns/quizzes/{quiz_id}/result/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "result": {
    "id": 1,
    "score": 80.0,
    "risk_level": "MEDIUM",
    "passed": true,
    ...
  },
  "question_details": [
    {
      "id": 1,
      "question_number": 1,
      "email_template": {
        "subject": "Password Reset Required",
        "sender_name": "IT Support",
        "sender_email": "support@fake-company.com",
        "body": "...",
        "email_type": "PHISHING",
        "category": "CREDENTIAL_HARVESTING",
        "difficulty": "MEDIUM",
        "red_flags": [
          "Suspicious domain",
          "Urgency tactics"
        ],
        "explanation": "This email shows classic phishing indicators..."
      },
      "answer": "PHISHING",
      "is_correct": true,
      "correct_answer": "PHISHING",
      "time_spent_seconds": 45,
      "requires_training": false
    },
    ...
  ]
}
```

### Campaign Analytics

#### Get Campaign Statistics

```http
GET /api/v1/campaigns/campaigns/{id}/statistics/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "campaign_id": 1,
  "campaign_name": "Q1 2024 Phishing Awareness",
  "status": "ACTIVE",
  "total_participants": 50,
  "completed_participants": 45,
  "completion_rate": 90.0,
  "average_score": 75.5,
  "total_emails": 10,
  "phishing_emails": 5,
  "legitimate_emails": 5,
  "risk_distribution": {
    "low": 20,
    "medium": 18,
    "high": 5,
    "critical": 2
  },
  "top_performers": [...],
  "needs_training": [...]
}
```

## Data Models

### Campaign

- **name**: Campaign name (multilingual)
- **company**: Foreign key to Company
- **created_by**: Company admin who created it
- **num_emails**: Total emails in quiz (5-50)
- **phishing_ratio**: Percentage of phishing emails (0.2-0.8)
- **status**: DRAFT, ACTIVE, SCHEDULED, COMPLETED, ARCHIVED
- **start_date/end_date**: Campaign timeframe
- **Statistics**: total_participants, completed_participants, average_score

### Quiz

- **campaign**: Foreign key to Campaign
- **employee**: Foreign key to User (employee)
- **status**: NOT_STARTED, IN_PROGRESS, COMPLETED
- **current_question_index**: Progress tracker
- **started_at/completed_at**: Timestamps

### QuizResult

- **quiz**: One-to-one with Quiz
- **score**: Percentage score (0-100)
- **correct_answers/incorrect_answers**: Count metrics
- **phishing_emails_identified/missed**: Phishing detection metrics
- **false_positives**: Legitimate emails marked as phishing
- **time_taken_seconds**: Total time
- **risk_level**: LOW, MEDIUM, HIGH, CRITICAL
- **passed**: Boolean (score >= 70%)

### EmailTemplate

- **campaign**: Foreign key to Campaign
- **sender_name/sender_email/subject/body**: Email content
- **email_type**: PHISHING or LEGITIMATE
- **category**: Specific attack type or legitimate category
- **difficulty**: EASY, MEDIUM, HARD
- **is_ai_generated**: Boolean flag
- **red_flags**: JSON list of phishing indicators
- **explanation**: Educational content about why it's phishing/legitimate

### QuizQuestion

- **quiz**: Foreign key to Quiz
- **email_template**: Foreign key to EmailTemplate
- **question_number**: Order in quiz
- **answer**: Employee's answer (PHISHING/LEGITIMATE)
- **is_correct**: Boolean
- **confidence_level**: 1-5 scale
- **time_spent_seconds**: Time on this question
- **requires_training**: Flag for incorrect phishing detection

## Risk Level Calculation

Risk levels are determined based on quiz performance:

```python
if score >= 90 and phishing_missed == 0:
    risk_level = 'LOW'
elif score >= 70 and phishing_missed <= 1:
    risk_level = 'MEDIUM'
elif score >= 50 or phishing_missed <= 3:
    risk_level = 'HIGH'
else:
    risk_level = 'CRITICAL'
```

## Permission Model

- **Super Admin**: Full access to all campaigns
- **Company Admin**: Create, manage campaigns for their company; view all employee results
- **Employee**: View and take assigned quizzes; view own results only
- **Public User**: No access to campaigns

## Integration with AI Model

The current implementation includes a placeholder for AI integration at:

```
POST /api/v1/assessments/ai/generate-emails/
```

To integrate your PyTorch LSTM model:

1. Replace `_generate_sample_phishing_emails()` and `_generate_sample_legitimate_emails()` methods in `apps/assessments/views.py`

2. Load your trained model and call it:

```python
def _generate_sample_phishing_emails(self, campaign, count, language):
    # Load your PyTorch model
    import torch
    model = torch.load('path/to/your/lstm_model.pth')
    model.eval()

    # Generate emails using your model
    generated_emails = []
    for i in range(count):
        # Your generation logic here
        email_text = model.generate(...)

        # Create EmailTemplate instance
        email = EmailTemplate.objects.create(
            campaign=campaign,
            # ... populate fields from generated content
            is_ai_generated=True,
            ai_model_used='Your Model Name'
        )
        generated_emails.append(EmailTemplateSerializer(email).data)

    return generated_emails
```

3. Consider adding:
   - Model version tracking
   - Generation parameters logging
   - Quality validation before saving
   - Batch generation for efficiency

## Testing the Workflow

### 1. Create a Company and Users

```bash
# Via Django admin or API
# Create company
# Create company admin user
# Create employee users
```

### 2. Create a Campaign

```bash
curl -X POST http://localhost:8000/api/v1/campaigns/campaigns/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "company": 1,
    "num_emails": 10,
    "phishing_ratio": 0.5
  }'
```

### 3. Generate Emails

```bash
curl -X POST http://localhost:8000/api/v1/assessments/ai/generate-emails/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "num_phishing_emails": 5,
    "num_legitimate_emails": 5,
    "language": "en"
  }'
```

### 4. Activate and Assign

```bash
# Activate
curl -X POST http://localhost:8000/api/v1/campaigns/campaigns/1/activate/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Assign to employees
curl -X POST http://localhost:8000/api/v1/campaigns/campaigns/1/assign_to_employees/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"employee_ids": [5, 6, 7]}'
```

### 5. Take Quiz (as Employee)

```bash
# Start quiz
curl -X POST http://localhost:8000/api/v1/campaigns/quizzes/1/start/ \
  -H "Authorization: Bearer EMPLOYEE_TOKEN"

# Answer questions
curl -X POST http://localhost:8000/api/v1/campaigns/quizzes/1/answer_question/ \
  -H "Authorization: Bearer EMPLOYEE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_number": 1,
    "answer": "PHISHING",
    "confidence_level": 4,
    "time_spent_seconds": 30
  }'

# Submit quiz
curl -X POST http://localhost:8000/api/v1/campaigns/quizzes/1/submit/ \
  -H "Authorization: Bearer EMPLOYEE_TOKEN"
```

## Next Steps

1. **Integrate Real AI Model**: Replace sample generation with your trained PyTorch LSTM
2. **Add Company CRUD**: Create endpoints for company management
3. **Implement Training Module**: Auto-assign training based on quiz results
4. **Add Gamification**: Leaderboards and badges
5. **Build Analytics Dashboard**: Comprehensive reporting for admins
