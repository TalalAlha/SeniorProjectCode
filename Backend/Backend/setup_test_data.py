"""
PhishAware Test Data Setup Script
Run with: python manage.py shell < setup_test_data.py
Or copy/paste into: python manage.py shell
"""

import sys
from datetime import datetime, timedelta
from django.utils import timezone

print("=" * 60)
print("PhishAware Test Data Setup")
print("=" * 60)

# ============================================================
# 1. CREATE COMPANY
# ============================================================
print("\n[1/6] Creating Company...")

from apps.companies.models import Company

company, created = Company.objects.get_or_create(
    name='Acme Corporation',
    defaults={
        'name_ar': 'شركة أكمي',
        'description': 'Test company for PhishAware testing',
        'description_ar': 'شركة تجريبية لاختبار PhishAware',
        'email': 'contact@acme.com',
        'phone': '+1234567890',
        'industry': 'TECH',
        'company_size': '51-200',
        'is_active': True,
        'subscription_start_date': timezone.now().date(),
        'subscription_end_date': (timezone.now() + timedelta(days=365)).date(),
    }
)
print(f"  Company: {company.name} ({'created' if created else 'exists'})")

# ============================================================
# 2. CREATE USERS
# ============================================================
print("\n[2/6] Creating Users...")

from apps.accounts.models import User

users_data = [
    {
        'email': 'admin@acme.com',
        'first_name': 'John',
        'last_name': 'Manager',
        'role': 'COMPANY_ADMIN',
        'company': company,
    },
    {
        'email': 'alice@acme.com',
        'first_name': 'Alice',
        'last_name': 'Smith',
        'role': 'EMPLOYEE',
        'company': company,
    },
    {
        'email': 'bob@acme.com',
        'first_name': 'Bob',
        'last_name': 'Johnson',
        'role': 'EMPLOYEE',
        'company': company,
    },
    {
        'email': 'carol@acme.com',
        'first_name': 'Carol',
        'last_name': 'Williams',
        'role': 'EMPLOYEE',
        'company': company,
    },
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        email=user_data['email'],
        defaults={
            **user_data,
            'is_active': True,
            'is_verified': True,
        }
    )
    if created:
        user.set_password('TestPass123!')
        user.save()
    print(f"  User: {user.email} ({user.role}) - {'created' if created else 'exists'}")

admin = User.objects.get(email='admin@acme.com')

# ============================================================
# 3. CREATE SIMULATION TEMPLATES
# ============================================================
print("\n[3/6] Creating Simulation Templates...")

from apps.simulations.models import SimulationTemplate

templates_data = [
    {
        'name': 'IT Support Password Reset',
        'name_ar': 'إعادة تعيين كلمة المرور من الدعم التقني',
        'description': 'Fake IT support password reset request',
        'sender_name': 'IT Helpdesk',
        'sender_email': 'helpdesk@acme-support.com',
        'reply_to_email': 'helpdesk@acme-support.com',
        'subject': 'Urgent: Your Password Will Expire in 24 Hours',
        'body_html': '''<html><body>
<p>Dear {{employee_name}},</p>
<p>Your password will expire in 24 hours. Please click the link below to update your password immediately:</p>
<p><a href="{{phishing_link}}">Reset Password Now</a></p>
<p>Failure to update your password will result in account lockout.</p>
<p>Best regards,<br>IT Helpdesk</p>
</body></html>''',
        'body_plain': 'Dear {{employee_name}}, Your password expires in 24 hours. Click here to reset: {{phishing_link}}',
        'attack_vector': 'CREDENTIAL_HARVESTING',
        'difficulty': 'EASY',
        'requires_landing_page': True,
        'landing_page_title': 'Password Reset Portal',
        'landing_page_message': 'This was a phishing simulation. In a real attack, your credentials would have been stolen.',
        'landing_page_message_ar': 'كانت هذه محاكاة للتصيد. في هجوم حقيقي، كانت بياناتك ستُسرق.',
        'is_active': True,
        'is_public': True,
        'created_by': admin,
    },
    {
        'name': 'Prize Winner Notification',
        'name_ar': 'إشعار الفائز بالجائزة',
        'description': 'Fake lottery/prize notification',
        'sender_name': 'Rewards Department',
        'sender_email': 'rewards@prize-center.com',
        'subject': "Congratulations! You've Won a $500 Gift Card!",
        'body_html': '''<html><body>
<p>Dear {{employee_name}},</p>
<p>You have been randomly selected to receive a $500 gift card!</p>
<p><a href="{{phishing_link}}">Claim Your Prize Now</a></p>
<p>This offer expires in 24 hours.</p>
</body></html>''',
        'body_plain': 'You have won a $500 gift card! Claim here: {{phishing_link}}',
        'attack_vector': 'PRIZE_LOTTERY',
        'difficulty': 'EASY',
        'is_active': True,
        'is_public': True,
        'created_by': admin,
    },
    {
        'name': 'CEO Urgent Request',
        'name_ar': 'طلب عاجل من الرئيس التنفيذي',
        'description': 'Business Email Compromise - CEO impersonation',
        'sender_name': 'Michael Thompson (CEO)',
        'sender_email': 'm.thompson@acme-corp.net',
        'subject': 'Quick favor - time sensitive',
        'body_html': '''<html><body>
<p>Hi {{employee_name}},</p>
<p>I'm in a meeting and need you to handle something urgently. Please click the link below to review and approve the attached invoice.</p>
<p><a href="{{phishing_link}}">Review Invoice</a></p>
<p>Thanks,<br>Michael</p>
<p><small>Sent from my iPhone</small></p>
</body></html>''',
        'body_plain': 'Hi, I need you to review this invoice urgently: {{phishing_link}} - Michael',
        'attack_vector': 'BUSINESS_EMAIL_COMPROMISE',
        'difficulty': 'MEDIUM',
        'is_active': True,
        'is_public': True,
        'created_by': admin,
    },
]

for tmpl_data in templates_data:
    tmpl, created = SimulationTemplate.objects.get_or_create(
        name=tmpl_data['name'],
        defaults=tmpl_data
    )
    print(f"  Template: {tmpl.name} ({'created' if created else 'exists'})")

# ============================================================
# 4. CREATE TRAINING MODULES
# ============================================================
print("\n[4/6] Creating Training Modules...")

from apps.training.models import TrainingModule, TrainingQuestion

modules_data = [
    {
        'title': 'Introduction to Phishing Attacks',
        'title_ar': 'مقدمة في هجمات التصيد',
        'description': 'Learn the basics of identifying phishing emails',
        'description_ar': 'تعلم أساسيات التعرف على رسائل التصيد',
        'content_type': 'TEXT',
        'category': 'PHISHING_BASICS',
        'difficulty': 'BEGINNER',
        'content_html': '''<h1>What is Phishing?</h1>
<p>Phishing is a type of social engineering attack where attackers attempt to steal sensitive information by disguising themselves as trustworthy entities.</p>
<h2>Common Signs of Phishing</h2>
<ul>
<li>Urgent language creating panic</li>
<li>Suspicious sender email addresses</li>
<li>Generic greetings instead of your name</li>
<li>Spelling and grammar errors</li>
<li>Requests for sensitive information</li>
<li>Suspicious links or attachments</li>
</ul>''',
        'duration_minutes': 15,
        'passing_score': 80,
        'min_questions_required': 5,
        'score_reduction_on_pass': 15,
        'is_active': True,
        'is_mandatory': True,
        'created_by': admin,
        'questions': [
            {
                'question_number': 1,
                'question_text': 'What is phishing?',
                'question_text_ar': 'ما هو التصيد الاحتيالي؟',
                'options': ['A fishing technique', 'A cyber attack to steal credentials', 'A software update', 'A firewall setting'],
                'options_ar': ['تقنية صيد', 'هجوم إلكتروني لسرقة البيانات', 'تحديث برنامج', 'إعداد جدار حماية'],
                'correct_answer_index': 1,
                'explanation': 'Phishing is a cyber attack where attackers impersonate trusted entities to steal sensitive information.',
            },
            {
                'question_number': 2,
                'question_text': 'Which is a common sign of a phishing email?',
                'question_text_ar': 'ما هي العلامة الشائعة لرسالة تصيد؟',
                'options': ['Professional formatting', 'Urgent language creating panic', 'Company logo present', 'Proper grammar'],
                'options_ar': ['تنسيق احترافي', 'لغة عاجلة تسبب الذعر', 'وجود شعار الشركة', 'قواعد نحوية صحيحة'],
                'correct_answer_index': 1,
                'explanation': 'Phishing emails often use urgent language to pressure victims into acting without thinking.',
            },
            {
                'question_number': 3,
                'question_text': 'What should you do if you receive a suspicious email?',
                'question_text_ar': 'ماذا تفعل إذا تلقيت رسالة مشبوهة؟',
                'options': ['Click the link to verify', 'Reply asking for more info', 'Report it to IT security', 'Forward it to colleagues'],
                'options_ar': ['انقر على الرابط للتحقق', 'رد واطلب المزيد من المعلومات', 'أبلغ أمن تكنولوجيا المعلومات', 'أرسلها إلى الزملاء'],
                'correct_answer_index': 2,
                'explanation': 'Always report suspicious emails to your IT security team instead of interacting with them.',
            },
            {
                'question_number': 4,
                'question_text': 'Attackers often impersonate which entities?',
                'question_text_ar': 'من ينتحل المهاجمون هويتهم عادة؟',
                'options': ['Random strangers', 'Trusted organizations like banks or IT', 'Unknown foreign companies', 'Social media influencers'],
                'options_ar': ['غرباء عشوائيون', 'منظمات موثوقة مثل البنوك أو تكنولوجيا المعلومات', 'شركات أجنبية غير معروفة', 'مؤثرو وسائل التواصل الاجتماعي'],
                'correct_answer_index': 1,
                'explanation': 'Attackers impersonate trusted entities like banks, IT departments, or executives to gain trust.',
            },
            {
                'question_number': 5,
                'question_text': 'What is the safest action when unsure about an email?',
                'question_text_ar': 'ما هو الإجراء الأكثر أمانًا عند الشك في رسالة؟',
                'options': ['Open attachments to check', 'Click links to verify', 'Contact the sender through official channels', 'Ignore it completely'],
                'options_ar': ['افتح المرفقات للتحقق', 'انقر على الروابط للتحقق', 'اتصل بالمرسل عبر القنوات الرسمية', 'تجاهلها تمامًا'],
                'correct_answer_index': 2,
                'explanation': 'Contact the sender through known official channels (phone, official website) to verify legitimacy.',
            },
        ]
    },
    {
        'title': 'Identifying Malicious Links',
        'title_ar': 'التعرف على الروابط الخبيثة',
        'description': 'Learn how to identify and avoid malicious links',
        'description_ar': 'تعلم كيفية التعرف على الروابط الخبيثة وتجنبها',
        'content_type': 'TEXT',
        'category': 'LINK_SAFETY',
        'difficulty': 'INTERMEDIATE',
        'content_html': '''<h1>Link Safety</h1>
<p>Malicious links are one of the most common attack vectors in phishing emails.</p>
<h2>How to Check Links</h2>
<ul>
<li>Hover over links to see the actual URL</li>
<li>Check for misspellings in domain names</li>
<li>Look for HTTPS and valid certificates</li>
<li>Be wary of shortened URLs</li>
</ul>''',
        'duration_minutes': 20,
        'passing_score': 80,
        'min_questions_required': 5,
        'score_reduction_on_pass': 15,
        'is_active': True,
        'is_mandatory': True,
        'created_by': admin,
        'questions': [
            {
                'question_number': 1,
                'question_text': 'How can you check where a link actually leads?',
                'options': ['Click it quickly', 'Hover over it without clicking', 'Copy and paste it', 'Ask a colleague'],
                'correct_answer_index': 1,
                'explanation': 'Hovering shows the actual URL destination without clicking.',
            },
            {
                'question_number': 2,
                'question_text': 'What is a sign of a malicious URL?',
                'options': ['Uses HTTPS', 'Has a company logo', 'Misspelled domain name', 'Ends in .com'],
                'correct_answer_index': 2,
                'explanation': 'Attackers often use misspelled domains like "g00gle.com" instead of "google.com".',
            },
            {
                'question_number': 3,
                'question_text': 'Why are URL shorteners risky?',
                'options': ['They are slower', 'They hide the actual destination', 'They cost money', 'They require login'],
                'correct_answer_index': 1,
                'explanation': 'Shortened URLs hide the true destination, which could be malicious.',
            },
            {
                'question_number': 4,
                'question_text': 'What does HTTPS indicate?',
                'options': ['The site is fast', 'The connection is encrypted', 'The site is government-approved', 'The site is free'],
                'correct_answer_index': 1,
                'explanation': 'HTTPS means the connection is encrypted, but doesn\'t guarantee the site is legitimate.',
            },
            {
                'question_number': 5,
                'question_text': 'You receive a link claiming to be from your bank. What should you do?',
                'options': ['Click it immediately', 'Type the bank URL manually in your browser', 'Forward it to friends', 'Reply to verify'],
                'correct_answer_index': 1,
                'explanation': 'Always navigate to known websites directly by typing the URL yourself.',
            },
        ]
    },
    {
        'title': 'Protecting Your Credentials',
        'title_ar': 'حماية بياناتك الاعتمادية',
        'description': 'Best practices for credential security',
        'description_ar': 'أفضل الممارسات لأمان بيانات الاعتماد',
        'content_type': 'TEXT',
        'category': 'CREDENTIAL_PROTECTION',
        'difficulty': 'INTERMEDIATE',
        'content_html': '''<h1>Credential Security</h1>
<p>Your credentials are the keys to your digital life. Protect them!</p>
<h2>Best Practices</h2>
<ul>
<li>Never share passwords via email</li>
<li>Use unique passwords for each account</li>
<li>Enable multi-factor authentication</li>
<li>Use a password manager</li>
</ul>''',
        'duration_minutes': 25,
        'passing_score': 80,
        'min_questions_required': 5,
        'score_reduction_on_pass': 15,
        'is_active': True,
        'is_mandatory': True,
        'created_by': admin,
        'questions': [
            {
                'question_number': 1,
                'question_text': 'Should you ever share your password via email?',
                'options': ['Yes, if IT asks', 'Yes, if urgent', 'No, never', 'Yes, if encrypted'],
                'correct_answer_index': 2,
                'explanation': 'Never share passwords via email. Legitimate IT will never ask for your password.',
            },
            {
                'question_number': 2,
                'question_text': 'What is multi-factor authentication (MFA)?',
                'options': ['Using multiple passwords', 'Requiring additional verification beyond password', 'Logging in from multiple devices', 'Having multiple accounts'],
                'correct_answer_index': 1,
                'explanation': 'MFA requires something you know (password) plus something you have (phone) or are (fingerprint).',
            },
            {
                'question_number': 3,
                'question_text': 'Why use different passwords for different accounts?',
                'options': ['It is the law', 'If one is compromised, others remain safe', 'It is faster', 'Websites require it'],
                'correct_answer_index': 1,
                'explanation': 'Unique passwords prevent credential stuffing attacks across multiple accounts.',
            },
            {
                'question_number': 4,
                'question_text': 'What is a password manager?',
                'options': ['A person who manages passwords', 'Software that securely stores passwords', 'A browser feature only', 'An email service'],
                'correct_answer_index': 1,
                'explanation': 'Password managers securely store and generate unique passwords for all your accounts.',
            },
            {
                'question_number': 5,
                'question_text': 'A website asks for your password to "verify your account". What do you do?',
                'options': ['Enter it quickly', 'Check if it is the legitimate site first', 'Enter a fake password', 'Close the browser'],
                'correct_answer_index': 1,
                'explanation': 'Always verify you are on the legitimate website before entering any credentials.',
            },
        ]
    },
]

for module_data in modules_data:
    questions_data = module_data.pop('questions')
    module, created = TrainingModule.objects.get_or_create(
        title=module_data['title'],
        defaults=module_data
    )
    print(f"  Module: {module.title} ({'created' if created else 'exists'})")

    if created:
        for q_data in questions_data:
            TrainingQuestion.objects.create(module=module, **q_data)
        print(f"    Added {len(questions_data)} questions")

# ============================================================
# 5. CREATE/VERIFY BADGES
# ============================================================
print("\n[5/6] Verifying Badges...")

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
    badge, created = Badge.objects.get_or_create(
        badge_type=badge_data['badge_type'],
        defaults=badge_data
    )
    print(f"  Badge: {badge.name} ({'created' if created else 'exists'})")

# ============================================================
# 6. SUMMARY
# ============================================================
print("\n[6/6] Summary...")
print("\n" + "=" * 60)
print("TEST DATA SETUP COMPLETE!")
print("=" * 60)

from apps.companies.models import Company
from apps.accounts.models import User
from apps.simulations.models import SimulationTemplate
from apps.training.models import TrainingModule, TrainingQuestion
from apps.gamification.models import Badge

print(f"""
Created/Verified:
  - Companies: {Company.objects.count()}
  - Users: {User.objects.count()}
  - Simulation Templates: {SimulationTemplate.objects.count()}
  - Training Modules: {TrainingModule.objects.count()}
  - Training Questions: {TrainingQuestion.objects.count()}
  - Badges: {Badge.objects.count()}

Test Credentials:
  - Company Admin: admin@acme.com / TestPass123!
  - Employee 1: alice@acme.com / TestPass123!
  - Employee 2: bob@acme.com / TestPass123!
  - Employee 3: carol@acme.com / TestPass123!

Next Steps:
  1. Start the server: python manage.py runserver
  2. Test login: curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" -d '{{"email": "admin@acme.com", "password": "TestPass123!"}}'
  3. Follow TESTING_GUIDE.md for comprehensive testing
""")
