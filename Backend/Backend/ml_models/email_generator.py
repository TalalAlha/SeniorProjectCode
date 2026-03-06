"""
email_generator.py — PhishAware v2 AI email generation.

Loads the trained LSTM models once (lazy, thread-safe) and exposes:
  - EmailGenerator.generate_email(email_type, language)
  - generate_campaign_emails(campaign, num_phishing, num_legitimate)
"""

import json
import logging
import os
import random
import re
import threading

import torch

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Sender pools
# ---------------------------------------------------------------------------

_PHISHING_SENDERS_EN = [
    ("PayPal Security Team",       "security@paypal-account-verify.net"),
    ("Bank Alert System",          "noreply@secure-banking-alert.com"),
    ("Google Account Security",    "accounts@google-secure-verify.net"),
    ("Microsoft Support",          "support@microsoft-account-alert.com"),
    ("Amazon Customer Service",    "orders@amazon-verify-secure.com"),
    ("IT Security Department",     "security@it-alerts-verify.com"),
    ("Account Services",           "accounts@verify-login-secure.net"),
]

_PHISHING_SENDERS_AR = [
    ("فريق أمان البنك",            "security@alrajhi-alert.com"),
    ("خدمة العملاء",               "support@bank-secure-alert.net"),
    ("إدارة الحسابات",             "accounts@verify-secure.com"),
    ("فريق الحماية",               "protection@bank-alert.net"),
    ("الدعم الأمني",               "secure@account-verify-sa.com"),
]

_LEGIT_SENDERS_EN = [
    ("IT Department",              "it@company.com"),
    ("HR Team",                    "hr@company.com"),
    ("Management",                 "management@company.com"),
    ("Support Team",               "support@company.com"),
    ("Finance Department",         "finance@company.com"),
]

_LEGIT_SENDERS_AR = [
    ("قسم تقنية المعلومات",        "it@company.sa"),
    ("الموارد البشرية",            "hr@company.sa"),
    ("الإدارة",                    "management@company.sa"),
    ("فريق الدعم",                 "support@company.sa"),
    ("الشؤون المالية",             "finance@company.sa"),
]

# ---------------------------------------------------------------------------
# Subject pools (fallback when extraction fails)
# ---------------------------------------------------------------------------

_PHISHING_SUBJECTS_EN = [
    "Urgent: Verify Your Account Immediately",
    "Security Alert: Unusual Activity Detected",
    "Action Required: Confirm Your Identity",
    "Your Account Has Been Temporarily Suspended",
    "Important: Update Your Password Now",
    "Suspicious Login Attempt Detected",
    "Final Notice: Account Verification Required",
]

_PHISHING_SUBJECTS_AR = [
    "تنبيه أمني: تحقق من حسابك",
    "عاجل: تم اكتشاف نشاط مشبوه",
    "تحذير: حسابك في خطر",
    "مطلوب: تحديث بيانات حسابك",
    "إشعار أمني هام",
    "تعليق مؤقت لحسابك",
    "عاجل: تأكيد هويتك مطلوب",
]

_LEGIT_SUBJECTS_EN = [
    "Monthly Team Newsletter",
    "Meeting Reminder: Team Sync Tomorrow",
    "HR Update: Policy Changes",
    "IT Maintenance Notice",
    "Upcoming Company Event",
    "Performance Review Schedule",
    "Office Closure Announcement",
]

_LEGIT_SUBJECTS_AR = [
    "النشرة الشهرية للفريق",
    "تذكير باجتماع: مزامنة الفريق",
    "تحديث الموارد البشرية",
    "إشعار صيانة تقنية المعلومات",
    "فعالية الشركة القادمة",
    "جدول مراجعة الأداء",
    "إعلان إغلاق المكتب",
]

# ---------------------------------------------------------------------------
# Category pools
# ---------------------------------------------------------------------------

_PHISHING_CATEGORIES = [
    'CREDENTIAL_HARVESTING',
    'LINK_MANIPULATION',
    'SPEAR_PHISHING',
    'BUSINESS_EMAIL_COMPROMISE',
    'CLONE_PHISHING',
]

_LEGIT_CATEGORIES = [
    'LEGITIMATE_BUSINESS',
    'LEGITIMATE_NOTIFICATION',
    'LEGITIMATE_PERSONAL',
]

# ---------------------------------------------------------------------------
# Red-flag pools (shown to employees after quiz)
# ---------------------------------------------------------------------------

_PHISHING_RED_FLAGS_EN = [
    "Urgent language pressuring immediate action",
    "Suspicious sender domain not matching the claimed organisation",
    "Request for personal or account credentials",
    "Generic greeting instead of your name",
    "Hover-over link mismatch",
]

_PHISHING_RED_FLAGS_AR = [
    "لغة عاجلة تضغط على اتخاذ إجراء فوري",
    "نطاق المُرسِل مشبوه ولا يتطابق مع الجهة المزعومة",
    "طلب بيانات شخصية أو بيانات حساب",
    "رابط مزيف أو مشبوه",
    "تحية عامة بدلاً من اسمك",
]

# ---------------------------------------------------------------------------
# Core generation helper (from training docs)
# ---------------------------------------------------------------------------

_LABEL_STRIP_RE = re.compile(r'\[PHISH\]|\[LEGIT\]')


def _generate_sample(model, vocab, device, email_type='phishing',
                     max_len=120, temperature=0.8):
    model.eval()
    with torch.no_grad():
        tokens = [vocab.word2idx.get(vocab.START_TOKEN, 1)]
        if email_type == 'phishing' and '[PHISH]' in vocab.word2idx:
            tokens.append(vocab.word2idx['[PHISH]'])
        elif email_type == 'legitimate' and '[LEGIT]' in vocab.word2idx:
            tokens.append(vocab.word2idx['[LEGIT]'])

        hidden = model.init_hidden(1, device)
        for token in tokens:
            x = torch.tensor([[token]], device=device)
            output, hidden = model(x, hidden)

        for _ in range(max_len):
            logits = output[0, -1] / temperature
            top_vals, top_ids = torch.topk(logits, 50)
            probs = torch.softmax(top_vals, dim=0)
            chosen_idx = torch.multinomial(probs, 1).item()
            next_token = top_ids[chosen_idx].item()
            if next_token == vocab.word2idx.get(vocab.END_TOKEN, 2):
                break
            if next_token == vocab.word2idx.get(vocab.PAD_TOKEN, 0):
                continue
            tokens.append(next_token)
            x = torch.tensor([[next_token]], device=device)
            output, hidden = model(x, hidden)

    raw = vocab.decode(tokens)
    # Strip label control tokens that appear at start of decoded text
    return _LABEL_STRIP_RE.sub('', raw).strip()


def _extract_subject(body: str, language: str) -> str:
    """Pull a subject line from the first sentence of the body (≤80 chars)."""
    # Split on common sentence terminators
    m = re.split(r'[.!?。،]', body, maxsplit=1)
    candidate = m[0].strip() if m else ''
    # Keep only if it looks reasonable
    if 10 < len(candidate) <= 80:
        return candidate
    # Fall back to a fixed-length truncation of the body start
    if len(body) > 15:
        truncated = body[:75].rsplit(' ', 1)[0]
        if len(truncated) > 10:
            return truncated + '…'
    return ''   # caller will use fallback pool


def _pick_sender(email_type: str, language: str):
    if email_type == 'phishing':
        pool = _PHISHING_SENDERS_AR if language == 'ar' else _PHISHING_SENDERS_EN
    else:
        pool = _LEGIT_SENDERS_AR if language == 'ar' else _LEGIT_SENDERS_EN
    return random.choice(pool)


def _pick_subject(email_type: str, language: str, body: str) -> str:
    subject = _extract_subject(body, language)
    if subject:
        return subject
    if email_type == 'phishing':
        pool = _PHISHING_SUBJECTS_AR if language == 'ar' else _PHISHING_SUBJECTS_EN
    else:
        pool = _LEGIT_SUBJECTS_AR if language == 'ar' else _LEGIT_SUBJECTS_EN
    return random.choice(pool)


# ---------------------------------------------------------------------------
# EmailGenerator — loads models once, lazily, thread-safe
# ---------------------------------------------------------------------------

class EmailGenerator:
    def __init__(self):
        self._lock = threading.Lock()
        self._loaded = False
        self._en_model = None
        self._ar_model = None
        self._en_vocab = None
        self._ar_vocab = None
        self._config = None
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _load_models(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:   # double-checked locking
                return
            logger.info("Loading PhishAware v2 LSTM models onto %s …", self._device)
            from ml_models.vocabulary import Vocabulary
            from ml_models.lstm_model import EmailLSTM

            with open(os.path.join(_BASE_DIR, 'model_config.json'), 'r', encoding='utf-8') as f:
                self._config = json.load(f)

            cfg = self._config

            # --- English model ---
            self._en_vocab = Vocabulary.load(os.path.join(_BASE_DIR, 'vocab_en.json'))
            en_model = EmailLSTM(
                vocab_size=len(self._en_vocab),
                embedding_dim=cfg['embedding_dim'],
                hidden_dim=cfg['hidden_dim'],
                num_layers=cfg['num_layers'],
                dropout=cfg['dropout'],
            )
            en_model.load_state_dict(
                torch.load(
                    os.path.join(_BASE_DIR, 'phishing_lstm_en.pth'),
                    map_location=self._device,
                    weights_only=True,
                )
            )
            en_model.to(self._device).eval()
            self._en_model = en_model

            # --- Arabic model ---
            self._ar_vocab = Vocabulary.load(os.path.join(_BASE_DIR, 'vocab_ar.json'))
            ar_model = EmailLSTM(
                vocab_size=len(self._ar_vocab),
                embedding_dim=cfg['embedding_dim'],
                hidden_dim=cfg['hidden_dim'],
                num_layers=cfg['num_layers'],
                dropout=cfg['dropout'],
            )
            ar_model.load_state_dict(
                torch.load(
                    os.path.join(_BASE_DIR, 'phishing_lstm_ar.pth'),
                    map_location=self._device,
                    weights_only=True,
                )
            )
            ar_model.to(self._device).eval()
            self._ar_model = ar_model

            self._loaded = True
            logger.info("PhishAware v2 models loaded successfully.")

    def generate_email(self, email_type: str = 'phishing', language: str = 'en') -> dict:
        """
        Generate one AI email.

        Args:
            email_type: 'phishing' | 'legitimate'
            language:   'en' | 'ar'

        Returns:
            dict with keys: subject, body, sender_name, sender_email
        """
        self._load_models()

        if language == 'ar':
            model, vocab = self._ar_model, self._ar_vocab
            max_len = self._config.get('max_seq_len_ar', 100)
            temperature = 0.75
        else:
            model, vocab = self._en_model, self._en_vocab
            max_len = self._config.get('max_seq_len_en', 120)
            temperature = 0.8

        body = _generate_sample(model, vocab, self._device,
                                email_type=email_type,
                                max_len=max_len,
                                temperature=temperature)

        # Ensure minimum useful length; retry once with higher temperature
        if len(body.split()) < 15:
            body = _generate_sample(model, vocab, self._device,
                                    email_type=email_type,
                                    max_len=max_len,
                                    temperature=min(temperature + 0.15, 1.0))

        subject = _pick_subject(email_type, language, body)
        sender_name, sender_email = _pick_sender(email_type, language)

        return {
            'subject': subject,
            'body': body,
            'sender_name': sender_name,
            'sender_email': sender_email,
        }


# ---------------------------------------------------------------------------
# Django integration — called from CampaignViewSet.perform_create
# ---------------------------------------------------------------------------

def generate_campaign_emails(campaign, num_phishing: int, num_legitimate: int):
    """
    Generate and save EmailTemplate objects for a campaign.

    Args:
        campaign:       Campaign model instance
        num_phishing:   Number of phishing emails to generate
        num_legitimate: Number of legitimate emails to generate

    Returns:
        List of created EmailTemplate instances
    """
    from apps.assessments.models import EmailTemplate

    generator = _get_generator()
    templates = []

    # Determine language distribution from campaign's english_ratio (default 0.5)
    english_ratio = float(getattr(campaign, 'english_ratio', 0.5))

    phishing_en = round(num_phishing * english_ratio)
    phishing_ar = num_phishing - phishing_en
    legit_en = round(num_legitimate * english_ratio)
    legit_ar = num_legitimate - legit_en

    tasks = (
        [('phishing', 'en')] * phishing_en +
        [('phishing', 'ar')] * phishing_ar +
        [('legitimate', 'en')] * legit_en +
        [('legitimate', 'ar')] * legit_ar
    )
    random.shuffle(tasks)

    for email_type, language in tasks:
        try:
            data = generator.generate_email(email_type=email_type, language=language)
        except Exception as exc:
            logger.warning(
                "AI generation failed for (%s, %s): %s — skipping email",
                email_type, language, exc,
            )
            continue

        db_type = 'PHISHING' if email_type == 'phishing' else 'LEGITIMATE'

        category = (
            random.choice(_PHISHING_CATEGORIES)
            if email_type == 'phishing'
            else random.choice(_LEGIT_CATEGORIES)
        )

        red_flags = (
            random.sample(_PHISHING_RED_FLAGS_AR if language == 'ar' else _PHISHING_RED_FLAGS_EN,
                          k=min(3, len(_PHISHING_RED_FLAGS_EN)))
            if email_type == 'phishing'
            else []
        )

        template = EmailTemplate.objects.create(
            campaign=campaign,
            sender_name=data['sender_name'],
            sender_email=data['sender_email'],
            subject=data['subject'],
            body=data['body'],
            email_type=db_type,
            category=category,
            difficulty=_pick_difficulty(),
            language=language,
            is_ai_generated=True,
            ai_model_used='PhishAware-LSTM-v2',
            generation_prompt=f'type={email_type}, language={language}',
            red_flags=red_flags,
        )
        templates.append(template)

    logger.info(
        "Campaign '%s': created %d/%d AI email templates.",
        campaign.name, len(templates), num_phishing + num_legitimate,
    )
    return templates


def _pick_difficulty() -> str:
    """Weighted random difficulty: 30% EASY, 50% MEDIUM, 20% HARD."""
    return random.choices(['EASY', 'MEDIUM', 'HARD'], weights=[30, 50, 20])[0]


# ---------------------------------------------------------------------------
# Module-level singleton — lazy, created on first use
# ---------------------------------------------------------------------------

_generator_instance: EmailGenerator | None = None
_generator_lock = threading.Lock()


def _get_generator() -> EmailGenerator:
    global _generator_instance
    if _generator_instance is None:
        with _generator_lock:
            if _generator_instance is None:
                _generator_instance = EmailGenerator()
    return _generator_instance
