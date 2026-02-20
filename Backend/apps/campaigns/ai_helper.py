"""
AI Helper for Campaign Management
Generates EmailTemplate objects using the trained LSTM model
"""

import random
import logging

from ml_models.email_generator import email_generator
from apps.assessments.models import EmailTemplate

logger = logging.getLogger(__name__)

# Sender pools for realistic email generation
PHISHING_SENDERS = {
    'en': [
        ('IT Security Team', 'security-alert@account-verify.com'),
        ('Account Services', 'noreply@update-accounts.net'),
        ('Payment Processing', 'billing@payment-confirm.org'),
        ('Package Delivery', 'tracking@delivery-notice.com'),
        ('HR Department', 'hr-urgent@company-portal.net'),
    ],
    'ar': [
        ('فريق الأمان', 'security@absher-update.com'),
        ('خدمة العملاء', 'support@sadad-billing.net'),
        ('البريد السعودي', 'tracking@saudi-post-delivery.com'),
        ('الدعم التقني', 'admin@bank-sa-alert.com'),
        ('إدارة الحسابات', 'accounts@portal-verify.net'),
    ],
}

LEGITIMATE_SENDERS = {
    'en': [
        ('HR Department', 'hr@{domain}'),
        ('IT Support', 'it-support@{domain}'),
        ('Team Lead', 'team-updates@{domain}'),
        ('Training Department', 'training@{domain}'),
        ('Office Manager', 'office@{domain}'),
    ],
    'ar': [
        ('إدارة الموارد البشرية', 'hr@{domain}'),
        ('الدعم التقني', 'it-support@{domain}'),
        ('قائد الفريق', 'team-updates@{domain}'),
        ('إدارة التدريب', 'training@{domain}'),
        ('مدير المكتب', 'office@{domain}'),
    ],
}

PHISHING_CATEGORIES = [
    'SPEAR_PHISHING',
    'CREDENTIAL_HARVESTING',
    'LINK_MANIPULATION',
    'BUSINESS_EMAIL_COMPROMISE',
    'CLONE_PHISHING',
]

LEGITIMATE_CATEGORIES = [
    'LEGITIMATE_BUSINESS',
    'LEGITIMATE_NOTIFICATION',
    'LEGITIMATE_PERSONAL',
]

RED_FLAGS_MAP = {
    'SPEAR_PHISHING': {
        'en': ['Personalized greeting with urgency', 'Requests sensitive information', 'Unusual sender domain'],
        'ar': ['تحية شخصية مع إلحاح', 'يطلب معلومات حساسة', 'نطاق مرسل غير معتاد'],
    },
    'CREDENTIAL_HARVESTING': {
        'en': ['Asks for login credentials', 'Fake login page link', 'Threatens account suspension'],
        'ar': ['يطلب بيانات تسجيل الدخول', 'رابط صفحة تسجيل دخول مزيفة', 'يهدد بتعليق الحساب'],
    },
    'LINK_MANIPULATION': {
        'en': ['Suspicious URL', 'Mismatched link text and destination', 'Shortened URL hiding real domain'],
        'ar': ['رابط مشبوه', 'نص الرابط لا يتطابق مع الوجهة', 'رابط مختصر يخفي النطاق الحقيقي'],
    },
    'BUSINESS_EMAIL_COMPROMISE': {
        'en': ['Impersonates executive', 'Urgent financial request', 'Unusual request from management'],
        'ar': ['ينتحل شخصية مسؤول', 'طلب مالي عاجل', 'طلب غير معتاد من الإدارة'],
    },
    'CLONE_PHISHING': {
        'en': ['Copy of legitimate email with altered links', 'Claims to be a resend or update', 'Slightly modified sender address'],
        'ar': ['نسخة من بريد شرعي مع روابط معدلة', 'يدعي أنه إعادة إرسال أو تحديث', 'عنوان مرسل معدل قليلاً'],
    },
}

EXPLANATIONS_MAP = {
    'SPEAR_PHISHING': {
        'en': 'This is a spear phishing email targeting a specific individual. It uses personal details to appear legitimate while attempting to steal sensitive information.',
        'ar': 'هذا بريد تصيد موجه يستهدف شخصاً محدداً. يستخدم تفاصيل شخصية ليبدو شرعياً بينما يحاول سرقة معلومات حساسة.',
    },
    'CREDENTIAL_HARVESTING': {
        'en': 'This email attempts to harvest login credentials by directing the user to a fake login page. Legitimate organizations never ask for passwords via email.',
        'ar': 'يحاول هذا البريد جمع بيانات تسجيل الدخول عبر توجيه المستخدم لصفحة تسجيل دخول مزيفة. المنظمات الشرعية لا تطلب كلمات المرور عبر البريد.',
    },
    'LINK_MANIPULATION': {
        'en': 'This email contains manipulated links that appear legitimate but redirect to malicious websites. Always hover over links to verify the actual URL.',
        'ar': 'يحتوي هذا البريد على روابط معدلة تبدو شرعية لكنها تعيد التوجيه لمواقع خبيثة. تحقق دائماً من الرابط الفعلي قبل النقر.',
    },
    'BUSINESS_EMAIL_COMPROMISE': {
        'en': 'This email impersonates a company executive or authority figure to trick employees into performing actions like transferring funds or sharing confidential data.',
        'ar': 'ينتحل هذا البريد شخصية مسؤول في الشركة لخداع الموظفين لتنفيذ إجراءات مثل تحويل أموال أو مشاركة بيانات سرية.',
    },
    'CLONE_PHISHING': {
        'en': 'This is a clone of a legitimate email with altered links or attachments. The attacker replaces safe content with malicious versions.',
        'ar': 'هذا نسخة من بريد شرعي مع روابط أو مرفقات معدلة. يستبدل المهاجم المحتوى الآمن بنسخ خبيثة.',
    },
}


def _get_company_domain(company_name):
    """Derive a plausible email domain from company name."""
    clean = company_name.lower().replace(' ', '').replace('.', '')
    return f"{clean}.com"


def _pick_sender(email_type, language, company_domain):
    """Pick a random sender name and email for the given type/language."""
    if email_type == 'phishing':
        name, email = random.choice(PHISHING_SENDERS[language])
    else:
        name, email_tpl = random.choice(LEGITIMATE_SENDERS[language])
        email = email_tpl.format(domain=company_domain)
    return name, email


def generate_campaign_emails(campaign, num_phishing=5, num_legitimate=5):
    """
    Generate EmailTemplate objects for a campaign using the AI model.

    Creates phishing and legitimate EmailTemplate records attached to the
    campaign.  The existing quiz system (_generate_quiz_questions) will
    pull from campaign.email_templates when employees are assigned.

    Args:
        campaign: Campaign instance (already saved)
        num_phishing: Number of phishing emails to generate
        num_legitimate: Number of legitimate emails to generate

    Returns:
        List of created EmailTemplate instances
    """
    company_name = campaign.company.name
    company_domain = _get_company_domain(company_name)
    created_templates = []

    # --- Phishing emails ---
    for i in range(num_phishing):
        language = 'en' if i % 2 == 0 else 'ar'
        category = PHISHING_CATEGORIES[i % len(PHISHING_CATEGORIES)]

        # Generate via AI
        email_data = email_generator.generate_email(
            email_type='phishing',
            language=language,
            employee_name='{employee_name}',
            company_name=company_name,
        )

        sender_name, sender_email = _pick_sender('phishing', language, company_domain)

        template = EmailTemplate.objects.create(
            campaign=campaign,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=email_data['subject'],
            body=email_data['body'],
            email_type='PHISHING',
            category=category,
            difficulty=random.choice(['EASY', 'MEDIUM', 'HARD']),
            language=language,
            is_ai_generated=True,
            ai_model_used='PhishAware LSTM',
            red_flags=RED_FLAGS_MAP.get(category, {}).get(language, []),
            explanation=EXPLANATIONS_MAP.get(category, {}).get('en', ''),
            explanation_ar=EXPLANATIONS_MAP.get(category, {}).get('ar', ''),
        )
        created_templates.append(template)

    # --- Legitimate emails ---
    for i in range(num_legitimate):
        language = 'en' if i % 2 == 0 else 'ar'
        category = LEGITIMATE_CATEGORIES[i % len(LEGITIMATE_CATEGORIES)]

        email_data = email_generator.generate_email(
            email_type='legitimate',
            language=language,
            employee_name='{employee_name}',
            company_name=company_name,
        )

        sender_name, sender_email = _pick_sender('legitimate', language, company_domain)

        template = EmailTemplate.objects.create(
            campaign=campaign,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=email_data['subject'],
            body=email_data['body'],
            email_type='LEGITIMATE',
            category=category,
            difficulty='EASY',
            language=language,
            is_ai_generated=True,
            ai_model_used='PhishAware LSTM',
        )
        created_templates.append(template)

    logger.info(
        "Generated %d AI emails (%d phishing, %d legitimate) for campaign '%s'",
        len(created_templates), num_phishing, num_legitimate, campaign.name,
    )
    return created_templates


def generate_single_email(email_type, language, employee_name, company_name):
    """Generate a single email dict (subject, body, language, type)."""
    return email_generator.generate_email(
        email_type=email_type,
        language=language,
        employee_name=employee_name,
        company_name=company_name,
    )
