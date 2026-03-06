"""
Management command: seed_simulation_templates

Populates the database with 15 pre-built phishing simulation templates
(8 English + 7 Arabic) covering diverse attack vectors and difficulty levels.

Usage:
    python manage.py seed_simulation_templates
    python manage.py seed_simulation_templates --clear   # remove then re-seed
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import SimulationTemplate


TEMPLATES = [
    # =========================================================================
    # ENGLISH TEMPLATES
    # =========================================================================
    {
        'name': 'PayPal Account Verification',
        'name_ar': '',
        'description': 'Fake PayPal security alert demanding immediate account verification.',
        'description_ar': '',
        'sender_name': 'PayPal Security Team',
        'sender_email': 'security@paypa1-support.com',
        'reply_to_email': 'noreply@paypa1-support.com',
        'subject': 'Action Required: Verify Your PayPal Account Within 24 Hours',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
  <div style="background:#003087;padding:20px;text-align:center;">
    <span style="color:#fff;font-size:28px;font-weight:bold;">PayPal</span>
  </div>
  <div style="padding:30px;">
    <h2 style="color:#333;">Your Account Has Been Limited</h2>
    <p style="color:#555;">Dear Valued Customer,</p>
    <p style="color:#555;">We have detected <strong>unusual activity</strong> on your PayPal account. To protect you, we have temporarily limited your account access.</p>
    <p style="color:#555;"><strong>You must verify your information within 24 hours or your account will be permanently suspended.</strong></p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{LURE_LINK}" style="background:#0070ba;color:#fff;padding:15px 35px;text-decoration:none;border-radius:4px;font-size:16px;font-weight:bold;display:inline-block;">Verify Account Now</a>
    </div>
    <p style="color:#999;font-size:12px;">If you do not verify within 24 hours, your account will be permanently closed. This link expires soon.</p>
    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <p style="color:#999;font-size:11px;">PayPal, Inc. | 2211 North First Street | San Jose, CA 95131</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'Your PayPal account has been limited. Verify your account within 24 hours to avoid permanent suspension. Click here: {LURE_LINK}',
        'attack_vector': 'URGENCY_SCAM',
        'difficulty': 'MEDIUM',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. This was a security awareness test conducted by your organization. Real PayPal emails come from paypal.com domains, never from misspelled addresses like "paypa1-support.com".',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي محاكى. كان هذا اختبار توعية أمنية. رسائل PayPal الحقيقية تأتي من نطاقات paypal.com فقط.',
        'red_flags': [
            'Sender domain is "paypa1-support.com" (not paypal.com)',
            'Urgent 24-hour deadline to create panic',
            'Threat of permanent account suspension',
            'Generic greeting "Dear Valued Customer"',
            'Unusual link destination on hover',
        ],
    },

    {
        'name': 'Microsoft 365 Password Expiry',
        'name_ar': '',
        'description': 'IT impersonation email claiming the employee\'s Microsoft 365 password is about to expire.',
        'description_ar': '',
        'sender_name': 'IT Help Desk',
        'sender_email': 'helpdesk@microsoft-365security.net',
        'reply_to_email': '',
        'subject': 'URGENT: Your Microsoft 365 Password Expires in 2 Hours',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#f3f2f1;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;border:1px solid #ddd;">
  <div style="background:#0078d4;padding:16px 24px;display:flex;align-items:center;">
    <span style="color:#fff;font-size:22px;font-weight:600;">Microsoft</span>
  </div>
  <div style="padding:32px 24px;">
    <p style="color:#323130;font-size:16px;">Hi {EMPLOYEE_NAME},</p>
    <p style="color:#323130;">Your Microsoft 365 password is set to expire in <strong style="color:#d13438;">2 hours</strong>. You must update it immediately to continue accessing your email, Teams, and SharePoint.</p>
    <p style="color:#323130;"><strong>Failure to update your password will lock you out of all Microsoft services.</strong></p>
    <div style="background:#f3f2f1;border-left:4px solid #0078d4;padding:16px;margin:20px 0;border-radius:2px;">
      <p style="margin:0;color:#323130;font-size:14px;">Account: {EMPLOYEE_EMAIL}</p>
      <p style="margin:8px 0 0;color:#d13438;font-size:14px;font-weight:bold;">Password expires: TODAY</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#0078d4;color:#fff;padding:12px 28px;text-decoration:none;border-radius:2px;font-size:15px;font-weight:600;display:inline-block;">Update Password Now</a>
    </div>
    <p style="color:#605e5c;font-size:12px;">Microsoft IT Support | This is an automated security notification</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'Your Microsoft 365 password expires in 2 hours. Update it now: {LURE_LINK}',
        'attack_vector': 'AUTHORITY_IMPERSONATION',
        'difficulty': 'MEDIUM',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. This email impersonated Microsoft IT using a fake domain "microsoft-365security.net". Legitimate Microsoft emails always come from @microsoft.com domains.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. هذا البريد انتحل هوية Microsoft IT باستخدام نطاق مزيف.',
        'red_flags': [
            'Sender domain "microsoft-365security.net" is NOT microsoft.com',
            'Extreme urgency: "expires in 2 hours"',
            'Threat of complete service lockout',
            'Personalized with employee name/email to appear legitimate',
        ],
    },

    {
        'name': 'Amazon Order Cancellation Warning',
        'name_ar': '',
        'description': 'Fake Amazon shipping alert claiming a recent order will be cancelled if action is not taken.',
        'description_ar': '',
        'sender_name': 'Amazon Customer Service',
        'sender_email': 'order-alert@amaz0n-shipping.com',
        'reply_to_email': '',
        'subject': 'Your Recent Amazon Order Will Be Cancelled – Action Required',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f0f2f2;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;">
  <div style="background:#232f3e;padding:16px 24px;text-align:center;">
    <span style="color:#ff9900;font-size:24px;font-weight:bold;">amazon</span>
  </div>
  <div style="padding:28px 24px;">
    <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:16px;margin-bottom:20px;">
      <p style="margin:0;color:#856404;font-weight:bold;">⚠ Order Cancellation Warning</p>
    </div>
    <p style="color:#333;">Hello,</p>
    <p style="color:#333;">We were unable to process your recent order <strong>#112-4857293-6634211</strong> due to a billing verification issue.</p>
    <p style="color:#333;"><strong>Your order will be automatically cancelled in 48 hours unless you verify your payment information.</strong></p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#ff9900;color:#111;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">Verify Payment Now</a>
    </div>
    <p style="color:#666;font-size:13px;">Order Amount: $247.99 | Estimated Delivery: 2-3 business days</p>
    <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
    <p style="color:#999;font-size:11px;">Amazon.com | 410 Terry Ave. N. | Seattle, WA 98109</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'Your Amazon order #112-4857293-6634211 will be cancelled due to billing issues. Verify payment: {LURE_LINK}',
        'attack_vector': 'CREDENTIAL_HARVESTING',
        'difficulty': 'EASY',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. The sender address "amaz0n-shipping.com" uses a zero instead of "o" in Amazon. Always verify the exact domain before clicking links in emails.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. عنوان المرسل "amaz0n-shipping.com" يستخدم صفراً بدلاً من حرف o في Amazon.',
        'red_flags': [
            'Sender "amaz0n-shipping.com" uses zero instead of letter "o"',
            'Fake order number to create legitimacy',
            '48-hour deadline pressure tactic',
            'Generic "Hello" greeting instead of your name',
        ],
    },

    {
        'name': 'HR: Important Policy Update – Action Required',
        'name_ar': '',
        'description': 'Internal HR impersonation requesting employees to review and sign a new policy document.',
        'description_ar': '',
        'sender_name': 'Human Resources Department',
        'sender_email': 'hr-notifications@company-hr-portal.com',
        'reply_to_email': '',
        'subject': 'Required: Review and Sign New Employee Policy by Friday',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f8f9fa;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #dee2e6;border-radius:6px;overflow:hidden;">
  <div style="background:#4a5568;padding:16px 24px;">
    <p style="color:#fff;margin:0;font-size:18px;font-weight:bold;">Human Resources Department</p>
    <p style="color:#cbd5e0;margin:4px 0 0;font-size:13px;">Policy & Compliance Team</p>
  </div>
  <div style="padding:28px 24px;">
    <p style="color:#333;">Dear {EMPLOYEE_NAME},</p>
    <p style="color:#333;">We are rolling out an updated Employee Code of Conduct and Remote Work Policy effective <strong>next Monday</strong>. All employees are required to review and electronically sign the document before the deadline.</p>
    <p style="color:#e53e3e;font-weight:bold;">Employees who do not sign by Friday will have their system access temporarily suspended pending HR review.</p>
    <div style="border:1px solid #e2e8f0;border-radius:4px;padding:16px;margin:20px 0;background:#f7fafc;">
      <p style="margin:0 0 8px;font-weight:bold;color:#4a5568;">Document to Review:</p>
      <p style="margin:0;color:#718096;">📄 Employee Policy Update 2026.pdf</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#4a5568;color:#fff;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">Review & Sign Document</a>
    </div>
    <p style="color:#999;font-size:12px;">Human Resources | Confidential Communication</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'All employees must review and sign the new policy document by Friday or face system access suspension. Sign here: {LURE_LINK}',
        'attack_vector': 'AUTHORITY_IMPERSONATION',
        'difficulty': 'HARD',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. This email impersonated your HR department. The sender domain "company-hr-portal.com" is not your organization\'s domain. Internal policy updates always come from official company email addresses.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. انتحل هذا البريد هوية قسم الموارد البشرية. تحديثات السياسات الداخلية تأتي دائماً من عناوين البريد الرسمية للشركة.',
        'red_flags': [
            'Sender domain is not your company\'s official domain',
            'Threat of system access suspension creates fear',
            'Pressure to sign documents via email link',
            'Deadline pressure (by Friday)',
            'Legitimate HR never requests e-signatures via email links to external sites',
        ],
    },

    {
        'name': 'FedEx Package Delivery Failed – Reschedule Now',
        'name_ar': '',
        'description': 'Fake delivery notification claiming a package could not be delivered and requiring payment of a redelivery fee.',
        'description_ar': '',
        'sender_name': 'FedEx Delivery Service',
        'sender_email': 'tracking@fedex-deliverynow.net',
        'reply_to_email': '',
        'subject': 'FedEx: Delivery Failed – Small Fee Required to Redeliver',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;border:1px solid #ddd;">
  <div style="background:#4d148c;padding:16px 24px;text-align:center;">
    <span style="color:#ff6600;font-size:26px;font-weight:bold;">Fed</span><span style="color:#fff;font-size:26px;font-weight:bold;">Ex</span>
  </div>
  <div style="padding:28px 24px;">
    <div style="background:#fff3e0;border-left:4px solid #ff6600;padding:16px;margin-bottom:20px;">
      <p style="margin:0;font-weight:bold;color:#e65100;">⚠ Delivery Attempt Failed</p>
    </div>
    <p style="color:#333;">Dear Customer,</p>
    <p style="color:#333;">We attempted to deliver your package (Tracking: <strong>7489-2341-8892</strong>) but were unable to complete delivery.</p>
    <p style="color:#333;">To arrange redelivery, a small handling fee of <strong>$2.99</strong> is required. Please pay within 48 hours or your package will be returned to sender.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#ff6600;color:#fff;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">Pay $2.99 & Reschedule</a>
    </div>
    <p style="color:#999;font-size:12px;">FedEx | 942 South Shady Grove Road | Memphis, TN 38120</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'FedEx delivery failed for tracking #7489-2341-8892. Pay $2.99 redelivery fee: {LURE_LINK}',
        'attack_vector': 'CREDENTIAL_HARVESTING',
        'difficulty': 'EASY',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. FedEx and other delivery companies never require you to pay fees via email links. The sender "fedex-deliverynow.net" is not fedex.com. This is a common smishing/phishing tactic used to steal credit card information.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. شركات التوصيل لا تطلب رسوماً عبر روابط البريد الإلكتروني.',
        'red_flags': [
            'Sender "fedex-deliverynow.net" is not fedex.com',
            'Requesting payment for redelivery via email link (FedEx never does this)',
            'Fake tracking number to appear legitimate',
            'Small payment amount ($2.99) to seem low-risk',
            '48-hour deadline for urgency',
        ],
    },

    {
        'name': 'CEO Wire Transfer Request (BEC)',
        'name_ar': '',
        'description': 'Business Email Compromise (BEC) attack impersonating the CEO requesting an urgent wire transfer.',
        'description_ar': '',
        'sender_name': 'Ahmed Al-Rashid (CEO)',
        'sender_email': 'ceo@company-leadership-portal.com',
        'reply_to_email': 'ceo.requests@gmail.com',
        'subject': 'Confidential – Urgent Wire Transfer Required Today',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#fff;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;">
  <p style="color:#333;">Hi {EMPLOYEE_NAME},</p>
  <p style="color:#333;">I need your assistance with a time-sensitive matter. I am currently in a board meeting and cannot take calls.</p>
  <p style="color:#333;">We need to process an urgent wire transfer of <strong>$45,000</strong> to finalize a confidential acquisition. This must be completed today before 4 PM.</p>
  <p style="color:#333;">Please click below to access the secure transfer portal and process this immediately. Do not discuss this with anyone until the deal is announced.</p>
  <div style="text-align:center;margin:24px 0;">
    <a href="{LURE_LINK}" style="background:#1a365d;color:#fff;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">Access Secure Transfer Portal</a>
  </div>
  <p style="color:#333;">Regards,<br><strong>Ahmed Al-Rashid</strong><br>Chief Executive Officer</p>
</div>
</body>
</html>''',
        'body_plain': 'Urgent wire transfer of $45,000 needed today. Access transfer portal: {LURE_LINK} - Ahmed Al-Rashid, CEO',
        'attack_vector': 'BUSINESS_EMAIL_COMPROMISE',
        'difficulty': 'EXPERT',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. This is a Business Email Compromise (BEC) attack. Warning signs: the reply-to is a Gmail address (not company email), the sender domain is not your company\'s domain, and legitimate executives never request wire transfers via email without verification.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. هذا هجوم اختراق البريد الإلكتروني للأعمال (BEC). المديرون التنفيذيون الحقيقيون لا يطلبون تحويلات مصرفية عبر البريد الإلكتروني.',
        'red_flags': [
            'Reply-to is a personal Gmail address, not company email',
            'Sender domain is not the company\'s official domain',
            'Requesting secrecy ("Do not discuss with anyone")',
            'Urgent large financial transfer request',
            'CEO claiming unavailability to prevent phone verification',
        ],
    },

    {
        'name': 'IT Security: VPN Login Alert – Verify Identity',
        'name_ar': '',
        'description': 'IT security alert claiming suspicious VPN login from unknown location, requesting identity verification.',
        'description_ar': '',
        'sender_name': 'IT Security Operations',
        'sender_email': 'security-ops@it-security-monitor.net',
        'reply_to_email': '',
        'subject': '[SECURITY ALERT] Suspicious VPN Login Detected – Verify Now',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#1a1a2e;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:6px;overflow:hidden;">
  <div style="background:#c0392b;padding:16px 24px;text-align:center;">
    <p style="color:#fff;margin:0;font-size:18px;font-weight:bold;">🔴 SECURITY ALERT</p>
  </div>
  <div style="padding:28px 24px;">
    <p style="color:#333;">Hello {EMPLOYEE_NAME},</p>
    <p style="color:#333;">Our security systems have detected a <strong>suspicious VPN login</strong> to your account from an unrecognized location:</p>
    <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:4px;padding:16px;margin:16px 0;">
      <p style="margin:0 0 8px;color:#555;"><strong>Location:</strong> Moscow, Russia</p>
      <p style="margin:0 0 8px;color:#555;"><strong>IP Address:</strong> 185.220.101.47</p>
      <p style="margin:0 0 8px;color:#555;"><strong>Time:</strong> Today at 09:14 AM</p>
      <p style="margin:0;color:#c0392b;font-weight:bold;">Status: UNAUTHORIZED ACCESS ATTEMPT</p>
    </div>
    <p style="color:#333;">If this was not you, you must verify your identity immediately to secure your account.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#c0392b;color:#fff;padding:12px 28px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">Secure My Account Now</a>
    </div>
    <p style="color:#999;font-size:12px;">IT Security Operations Center | Automated Security Alert System</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'Suspicious VPN login detected from Moscow, Russia. Secure your account: {LURE_LINK}',
        'attack_vector': 'URGENCY_SCAM',
        'difficulty': 'HARD',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. This email used fear of a security breach to pressure you into clicking. Real IT security alerts come from your company\'s official domain, not "it-security-monitor.net". Always report suspicious emails to your IT team instead of clicking links.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. استخدم هذا البريد الخوف من خرق أمني لحملك على النقر. تنبيهات الأمان الحقيقية تأتي من نطاق شركتك الرسمي.',
        'red_flags': [
            'Sender domain "it-security-monitor.net" is not your company domain',
            'Fear-inducing content (security breach from Russia)',
            'Fabricated IP address and location details',
            'Pressure to click immediately without verifying via other channels',
        ],
    },

    {
        'name': 'LinkedIn: You Have a New Job Offer',
        'name_ar': '',
        'description': 'Fake LinkedIn notification claiming a recruiter has sent an exclusive job offer.',
        'description_ar': '',
        'sender_name': 'LinkedIn Jobs',
        'sender_email': 'jobs-notification@linkedln-careers.com',
        'reply_to_email': '',
        'subject': 'A top recruiter has sent you an exclusive job offer – View now',
        'body_html': '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f3f6f8;margin:0;padding:20px;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:6px;overflow:hidden;border:1px solid #dce6f1;">
  <div style="background:#0077b5;padding:16px 24px;">
    <span style="color:#fff;font-size:22px;font-weight:bold;">in</span>
    <span style="color:#fff;font-size:18px;font-weight:600;margin-left:8px;">LinkedIn</span>
  </div>
  <div style="padding:28px 24px;">
    <p style="color:#333;font-size:18px;font-weight:600;">You have 1 new job offer!</p>
    <p style="color:#555;">Hi {EMPLOYEE_NAME},</p>
    <p style="color:#555;">A top recruiter from <strong>Google</strong> has sent you an exclusive InMail about an exciting opportunity. This offer is available for the next <strong>48 hours only</strong>.</p>
    <div style="background:#f3f6f8;border-radius:4px;padding:16px;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:bold;color:#333;">Senior Software Engineer</p>
      <p style="margin:0 0 4px;color:#0077b5;">Google LLC · Mountain View, CA</p>
      <p style="margin:0;color:#555;font-size:13px;">💰 $180,000 - $250,000/year</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#0077b5;color:#fff;padding:12px 28px;text-decoration:none;border-radius:24px;font-size:15px;font-weight:bold;display:inline-block;">View Job Offer</a>
    </div>
    <p style="color:#999;font-size:12px;">LinkedIn Corporation | 1000 W Maude Ave, Sunnyvale, CA 94085</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'You have a new exclusive job offer from Google on LinkedIn. View it here: {LURE_LINK}',
        'attack_vector': 'PRIZE_LOTTERY',
        'difficulty': 'MEDIUM',
        'language': 'en',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'Security Awareness Alert',
        'landing_page_message': 'You clicked a simulated phishing link. The sender "linkedln-careers.com" misspells LinkedIn (note the extra "l"). Phishing emails often use enticing offers like high-paying jobs or prizes to lure victims. Always check LinkedIn directly through your browser.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد. "linkedln-careers.com" يهجئ LinkedIn بشكل خاطئ. تستخدم رسائل التصيد عروضاً مغرية لاستدراج الضحايا.',
        'red_flags': [
            'Sender "linkedln-careers.com" misspells "LinkedIn" (extra "l")',
            'Too-good-to-be-true job offer ($180K-$250K)',
            '48-hour urgency to prevent careful consideration',
            'Unverified Google recruiter claim',
        ],
    },

    # =========================================================================
    # ARABIC TEMPLATES
    # =========================================================================
    {
        'name': 'تنبيه أمني: التحقق من حساب البنك الأهلي',
        'name_ar': 'تنبيه أمني: التحقق من حساب البنك الأهلي',
        'description': 'Fake Saudi National Bank security alert demanding account verification.',
        'description_ar': 'تنبيه أمني مزيف من البنك الأهلي السعودي يطلب التحقق من الحساب.',
        'sender_name': 'البنك الأهلي السعودي - الأمن',
        'sender_email': 'security@albilad-bank-alert.com',
        'reply_to_email': '',
        'subject': 'عاجل: تم تعليق حسابك البنكي - تحقق الآن',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
  <div style="background:#006633;padding:20px;text-align:center;">
    <p style="color:#fff;font-size:22px;font-weight:bold;margin:0;">البنك الأهلي السعودي</p>
  </div>
  <div style="padding:30px;">
    <h2 style="color:#333;text-align:right;">تعليق مؤقت للحساب</h2>
    <p style="color:#555;text-align:right;">عزيزنا العميل،</p>
    <p style="color:#555;text-align:right;">تم رصد <strong>نشاط مشبوه</strong> على حسابك المصرفي. لحمايتك، تم تعليق الوصول إلى حسابك مؤقتاً.</p>
    <p style="color:#c0392b;font-weight:bold;text-align:right;"><strong>يجب عليك التحقق من هويتك خلال 24 ساعة وإلا سيتم إغلاق حسابك نهائياً.</strong></p>
    <div style="text-align:center;margin:30px 0;">
      <a href="{LURE_LINK}" style="background:#006633;color:#fff;padding:15px 35px;text-decoration:none;border-radius:4px;font-size:16px;font-weight:bold;display:inline-block;">تحقق من حسابك الآن</a>
    </div>
    <p style="color:#999;font-size:12px;text-align:right;">إذا لم تتحقق خلال 24 ساعة، سيتم إغلاق حسابك بشكل نهائي.</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'تم تعليق حسابك البنكي. يجب التحقق من هويتك خلال 24 ساعة. اضغط هنا: {LURE_LINK}',
        'attack_vector': 'URGENCY_SCAM',
        'difficulty': 'MEDIUM',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The sender domain "albilad-bank-alert.com" is not the official Saudi National Bank domain (alahli.com). Legitimate banks never suspend accounts via email or request verification through email links.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. نطاق المرسل "albilad-bank-alert.com" ليس النطاق الرسمي للبنك الأهلي السعودي (alahli.com). البنوك الحقيقية لا تعلق الحسابات عبر البريد الإلكتروني ولا تطلب التحقق من خلال روابط البريد.',
        'red_flags': [
            'نطاق المرسل "albilad-bank-alert.com" ليس النطاق الرسمي للبنك',
            'الضغط بالإلحاح (24 ساعة)',
            'التهديد بإغلاق الحساب نهائياً',
            'التحية العامة "عزيزنا العميل"',
            'رابط مشبوه عند التمرير فوقه',
        ],
    },

    {
        'name': 'رسالة عاجلة من مصلحة الزكاة والضريبة',
        'name_ar': 'رسالة عاجلة من مصلحة الزكاة والضريبة',
        'description': 'Fake ZATCA (Saudi tax authority) email claiming a tax refund is ready or penalty is due.',
        'description_ar': 'بريد إلكتروني مزيف من هيئة الزكاة والضريبة والجمارك يدعي وجود استرداد ضريبي أو غرامة.',
        'sender_name': 'هيئة الزكاة والضريبة والجمارك',
        'sender_email': 'refund@zatca-gov-sa.net',
        'reply_to_email': '',
        'subject': 'إشعار استرداد ضريبي: مبلغ 3,750 ريال في انتظار معالجته',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f0f8e8;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #ddd;">
  <div style="background:#1a5276;padding:20px;text-align:center;">
    <p style="color:#fff;font-size:20px;font-weight:bold;margin:0;">هيئة الزكاة والضريبة والجمارك</p>
    <p style="color:#aed6f1;font-size:14px;margin:4px 0 0;">المملكة العربية السعودية</p>
  </div>
  <div style="padding:28px 24px;">
    <div style="background:#d4efdf;border:1px solid #27ae60;border-radius:4px;padding:16px;margin-bottom:20px;text-align:right;">
      <p style="margin:0;font-weight:bold;color:#1e8449;">✓ استرداد ضريبي معتمد</p>
    </div>
    <p style="color:#333;text-align:right;">عزيزنا دافع الضرائب،</p>
    <p style="color:#333;text-align:right;">بعد مراجعة إقراراتك الضريبية، تم الموافقة على استرداد ضريبي بقيمة <strong>3,750 ريال سعودي</strong>.</p>
    <p style="color:#333;text-align:right;">يرجى تحديث بياناتك المصرفية خلال <strong>72 ساعة</strong> لاستلام المبلغ. بعد انقضاء هذه المدة، سيسقط حقك في الاسترداد.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#1a5276;color:#fff;padding:14px 32px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">استلام الاسترداد الضريبي</a>
    </div>
    <p style="color:#999;font-size:12px;text-align:right;">هيئة الزكاة والضريبة والجمارك | هذا إشعار رسمي</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'تم الموافقة على استرداد ضريبي بقيمة 3,750 ريال. حدّث بياناتك المصرفية خلال 72 ساعة: {LURE_LINK}',
        'attack_vector': 'PRIZE_LOTTERY',
        'difficulty': 'MEDIUM',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The sender domain "zatca-gov-sa.net" is not the official ZATCA domain (zatca.gov.sa). Government refunds are never processed via email links.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. نطاق المرسل "zatca-gov-sa.net" ليس النطاق الرسمي للهيئة (zatca.gov.sa). المسترداتات الحكومية لا تُعالج أبداً عبر روابط البريد الإلكتروني. هيئة الزكاة والضريبة والجمارك الحقيقية لن تطلب منك تحديث بياناتك المصرفية عبر البريد الإلكتروني.',
        'red_flags': [
            'نطاق المرسل "zatca-gov-sa.net" ليس zatca.gov.sa الرسمي',
            'وعد بمبلغ مالي لاستدراج الضحية',
            'مهلة 72 ساعة لخلق الضغط',
            'طلب البيانات المصرفية عبر البريد الإلكتروني (الجهات الحكومية لا تفعل ذلك)',
        ],
    },

    {
        'name': 'تنبيه أمني: تسجيل دخول مشبوه إلى حساب أبشر',
        'name_ar': 'تنبيه أمني: تسجيل دخول مشبوه إلى حساب أبشر',
        'description': 'Fake Absher (Saudi e-government portal) security alert about unauthorized login.',
        'description_ar': 'تنبيه أمني مزيف من بوابة أبشر يدعي وجود تسجيل دخول غير مصرح به.',
        'sender_name': 'بوابة أبشر - الأمن الإلكتروني',
        'sender_email': 'security-alert@absher-gov.net',
        'reply_to_email': '',
        'subject': 'تحذير أمني: تم رصد دخول غير مصرح به على حسابك في أبشر',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
  <div style="background:#006400;padding:20px;text-align:center;">
    <p style="color:#fff;font-size:22px;font-weight:bold;margin:0;">🏛 بوابة أبشر</p>
    <p style="color:#90ee90;font-size:13px;margin:4px 0 0;">وزارة الداخلية - المملكة العربية السعودية</p>
  </div>
  <div style="padding:28px 24px;">
    <div style="background:#fdecea;border:1px solid #e74c3c;border-radius:4px;padding:16px;margin-bottom:20px;text-align:right;">
      <p style="margin:0;font-weight:bold;color:#c0392b;">⚠ تحذير أمني عاجل</p>
    </div>
    <p style="color:#333;text-align:right;">عزيزنا المستخدم،</p>
    <p style="color:#333;text-align:right;">تم رصد محاولة تسجيل دخول مشبوهة على حسابك في بوابة أبشر من موقع غير معتاد:</p>
    <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:4px;padding:16px;margin:16px 0;text-align:right;">
      <p style="margin:0 0 8px;color:#555;"><strong>الدولة:</strong> تركيا</p>
      <p style="margin:0 0 8px;color:#555;"><strong>الوقت:</strong> اليوم - 11:45 صباحاً</p>
      <p style="margin:0;color:#c0392b;font-weight:bold;">الحالة: وصول غير مصرح به</p>
    </div>
    <p style="color:#333;text-align:right;">إذا لم تكن أنت من قام بذلك، يجب عليك التحقق من هويتك فوراً لحماية حسابك وبياناتك الشخصية.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#006400;color:#fff;padding:14px 32px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">تأمين حسابي الآن</a>
    </div>
    <p style="color:#999;font-size:12px;text-align:right;">بوابة أبشر الإلكترونية | نظام التنبيهات الأمنية الآلي</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'تم رصد دخول مشبوه على حسابك في أبشر من تركيا. أمّن حسابك الآن: {LURE_LINK}',
        'attack_vector': 'URGENCY_SCAM',
        'difficulty': 'HARD',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The real Absher portal domain is absher.sa, not "absher-gov.net". This email used fear of unauthorized access to pressure you into clicking.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. النطاق الرسمي لبوابة أبشر هو absher.sa وليس "absher-gov.net". استخدم هذا البريد الخوف من الوصول غير المصرح به لحملك على النقر السريع دون التحقق. دائماً تحقق من النطاق قبل النقر على أي رابط.',
        'red_flags': [
            'نطاق المرسل "absher-gov.net" ليس النطاق الرسمي absher.sa',
            'إثارة الخوف من الوصول غير المصرح به',
            'بيانات دخول مفصلة (تركيا والوقت) لإضفاء المصداقية',
            'الضغط للنقر فوراً دون التحقق عبر القنوات الرسمية',
        ],
    },

    {
        'name': 'إشعار من stc: فاتورتك الشهرية جاهزة للدفع',
        'name_ar': 'إشعار من stc: فاتورتك الشهرية جاهزة للدفع',
        'description': 'Fake STC (Saudi Telecom) billing notice claiming account suspension if bill is not paid.',
        'description_ar': 'إشعار مزيف من شركة الاتصالات السعودية يدعي تعليق الخدمة إذا لم تُسدّد الفاتورة.',
        'sender_name': 'stc - فريق الفواتير',
        'sender_email': 'billing@stc-billing-portal.com',
        'reply_to_email': '',
        'subject': 'فاتورة stc المستحقة - تجنب قطع الخدمة فوراً',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #ddd;">
  <div style="background:#6a0dad;padding:20px;text-align:center;">
    <p style="color:#fff;font-size:28px;font-weight:bold;margin:0;font-style:italic;">stc</p>
  </div>
  <div style="padding:28px 24px;">
    <div style="background:#ffeeba;border:1px solid #ffc107;border-radius:4px;padding:16px;margin-bottom:20px;text-align:right;">
      <p style="margin:0;font-weight:bold;color:#856404;">⚠ فاتورة مستحقة الدفع</p>
    </div>
    <p style="color:#333;text-align:right;">عزيزنا العميل {EMPLOYEE_NAME}،</p>
    <p style="color:#333;text-align:right;">لا تزال فاتورتك لشهر يناير بمبلغ <strong>485 ريال سعودي</strong> غير مسددة.</p>
    <p style="color:#c0392b;font-weight:bold;text-align:right;"><strong>إذا لم يتم السداد خلال 48 ساعة، سيتم إيقاف خدمة الاتصالات والإنترنت.</strong></p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#6a0dad;color:#fff;padding:14px 32px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">سداد الفاتورة الآن</a>
    </div>
    <p style="color:#999;font-size:12px;text-align:right;">شركة الاتصالات السعودية (stc) | فريق خدمة العملاء</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'فاتورة stc المستحقة: 485 ريال. سدد الآن لتجنب قطع الخدمة: {LURE_LINK}',
        'attack_vector': 'URGENCY_SCAM',
        'difficulty': 'EASY',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The sender "stc-billing-portal.com" is not stc\'s official domain (stc.com.sa). STC sends bills through the MySTC app and official channels, never through external billing portals.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. نطاق المرسل "stc-billing-portal.com" ليس النطاق الرسمي لـ stc (stc.com.sa). ترسل stc الفواتير عبر تطبيق MySTC والقنوات الرسمية فقط، وليس عبر بوابات خارجية. تحقق دائماً من رسائل الدفع عبر التطبيق الرسمي مباشرةً.',
        'red_flags': [
            'نطاق المرسل "stc-billing-portal.com" ليس stc.com.sa الرسمي',
            'التهديد بقطع الخدمة خلال 48 ساعة',
            'طلب الدفع عبر رابط بريد إلكتروني (stc لا تفعل ذلك)',
            'مبلغ محدد لإضفاء المصداقية',
        ],
    },

    {
        'name': 'مشاركة مستند Google Drive: تقرير مهم يتطلب مراجعتك',
        'name_ar': 'مشاركة مستند Google Drive: تقرير مهم يتطلب مراجعتك',
        'description': 'Fake Google Drive sharing notification for an "important report" requiring login.',
        'description_ar': 'إشعار مشاركة مزيف من Google Drive لـ"تقرير مهم" يتطلب تسجيل الدخول.',
        'sender_name': 'Google Drive',
        'sender_email': 'drive-share@googledocs-sharing.com',
        'reply_to_email': '',
        'subject': 'تمت مشاركة تقرير المبيعات السنوي 2025 معك',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f8f9fa;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #ddd;">
  <div style="padding:20px 24px;border-bottom:1px solid #eee;">
    <span style="font-size:22px;font-weight:bold;color:#4285f4;">G</span>
    <span style="font-size:18px;font-weight:600;color:#555;margin-right:4px;">oogle Drive</span>
  </div>
  <div style="padding:28px 24px;">
    <p style="color:#333;text-align:right;">مرحباً {EMPLOYEE_NAME}،</p>
    <p style="color:#333;text-align:right;">شارك معك <strong>محمد الغامدي</strong> مستنداً مهماً:</p>
    <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:20px;margin:16px 0;text-align:right;">
      <p style="font-size:18px;margin:0 0 8px;">📊 تقرير المبيعات السنوي 2025.xlsx</p>
      <p style="margin:0;color:#666;font-size:13px;">تمت المشاركة للتو · مستند Excel</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#1a73e8;color:#fff;padding:14px 32px;text-decoration:none;border-radius:4px;font-size:15px;font-weight:bold;display:inline-block;">فتح المستند</a>
    </div>
    <p style="color:#999;font-size:12px;text-align:right;">Google LLC | 1600 Amphitheatre Parkway, Mountain View, CA 94043</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'شارك معك محمد الغامدي تقرير المبيعات السنوي 2025. افتح المستند هنا: {LURE_LINK}',
        'attack_vector': 'CREDENTIAL_HARVESTING',
        'difficulty': 'HARD',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The sender "googledocs-sharing.com" is not Google\'s domain (google.com). Phishing emails often impersonate Google Drive or Microsoft OneDrive sharing notifications to steal credentials.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. نطاق المرسل "googledocs-sharing.com" ليس نطاق Google (google.com). كثيراً ما تنتحل رسائل التصيد هوية إشعارات مشاركة Google Drive أو Microsoft OneDrive لسرقة بيانات تسجيل الدخول. رسائل Google Drive الحقيقية تأتي دائماً من @google.com.',
        'red_flags': [
            'نطاق المرسل "googledocs-sharing.com" ليس نطاق Google الرسمي',
            'اسم مشارك غير معروف أو غير متوقع',
            'الرابط لا يؤدي إلى drive.google.com عند التمرير فوقه',
            'طلب تسجيل الدخول مرة أخرى للوصول إلى المستند',
        ],
    },

    {
        'name': 'عرض وظيفي حصري من LinkedIn',
        'name_ar': 'عرض وظيفي حصري من LinkedIn',
        'description': 'Fake LinkedIn job offer notification in Arabic targeting professionals.',
        'description_ar': 'إشعار مزيف بعرض وظيفي من LinkedIn بالعربية يستهدف المحترفين.',
        'sender_name': 'LinkedIn للوظائف',
        'sender_email': 'jobs@linkedln-mena.com',
        'reply_to_email': '',
        'subject': 'مسؤول توظيف من أرامكو السعودية أرسل إليك عرضاً وظيفياً حصرياً',
        'body_html': '''<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f3f6f8;margin:0;padding:20px;direction:rtl;">
{TRACKING_PIXEL}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:6px;overflow:hidden;border:1px solid #dce6f1;">
  <div style="background:#0077b5;padding:16px 24px;text-align:right;">
    <span style="color:#fff;font-size:22px;font-weight:bold;">in</span>
    <span style="color:#fff;font-size:18px;font-weight:600;margin-right:8px;">LinkedIn</span>
  </div>
  <div style="padding:28px 24px;text-align:right;">
    <p style="color:#333;font-size:18px;font-weight:600;">لديك عرض وظيفي جديد!</p>
    <p style="color:#555;">مرحباً {EMPLOYEE_NAME}،</p>
    <p style="color:#555;">أرسل إليك مسؤول توظيف من <strong>أرامكو السعودية</strong> عرضاً وظيفياً حصرياً عبر InMail. هذا العرض متاح لـ <strong>48 ساعة فقط</strong>.</p>
    <div style="background:#f3f6f8;border-radius:4px;padding:16px;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:bold;color:#333;">مهندس بيانات أول</p>
      <p style="margin:0 0 4px;color:#0077b5;">أرامكو السعودية · الظهران، المملكة العربية السعودية</p>
      <p style="margin:0;color:#555;font-size:13px;">💰 40,000 - 65,000 ريال / شهرياً</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{LURE_LINK}" style="background:#0077b5;color:#fff;padding:12px 28px;text-decoration:none;border-radius:24px;font-size:15px;font-weight:bold;display:inline-block;">عرض العرض الوظيفي</a>
    </div>
    <p style="color:#999;font-size:12px;">LinkedIn Corporation | 1000 W Maude Ave, Sunnyvale, CA 94085</p>
  </div>
</div>
</body>
</html>''',
        'body_plain': 'لديك عرض وظيفي حصري من أرامكو السعودية على LinkedIn. اعرضه هنا: {LURE_LINK}',
        'attack_vector': 'PRIZE_LOTTERY',
        'difficulty': 'MEDIUM',
        'language': 'ar',
        'is_public': True,
        'requires_landing_page': True,
        'landing_page_title': 'تنبيه الوعي الأمني',
        'landing_page_message': 'You clicked a simulated phishing link. The sender "linkedln-mena.com" misspells LinkedIn. Phishing emails in Arabic often use prestigious Saudi companies like Aramco to make offers seem more credible.',
        'landing_page_message_ar': 'لقد نقرت على رابط تصيد احتيالي. نطاق "linkedln-mena.com" يهجئ LinkedIn بشكل خاطئ (حرف L إضافي). تستخدم رسائل التصيد العربية شركات سعودية مرموقة كأرامكو لجعل العروض تبدو أكثر مصداقية. تحقق دائماً من LinkedIn مباشرةً في متصفحك لا من روابط البريد الإلكتروني.',
        'red_flags': [
            'نطاق المرسل "linkedln-mena.com" يهجئ LinkedIn بشكل خاطئ (حرف L زائد)',
            'عرض وظيفي لا يُصدَّق براتب مرتفع جداً',
            'مهلة 48 ساعة لمنع التفكير المتأني',
            'ادعاء غير مُتحقَّق منه بأن المرسِل من أرامكو السعودية',
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed phishing simulation templates (EN + AR) into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing global templates before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = SimulationTemplate.objects.filter(company__isnull=True).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing global templates.'))

        created_count = 0
        skipped_count = 0

        for tpl_data in TEMPLATES:
            template, created = SimulationTemplate.objects.get_or_create(
                name=tpl_data['name'],
                language=tpl_data['language'],
                company=None,
                defaults=tpl_data,
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {template.name} [{template.language.upper()}]')
                )
            else:
                skipped_count += 1
                self.stdout.write(f'  - Skipped (already exists): {template.name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {created_count} templates, skipped {skipped_count} existing.'
        ))
        self.stdout.write(
            f'Total templates in DB: {SimulationTemplate.objects.count()}'
        )
