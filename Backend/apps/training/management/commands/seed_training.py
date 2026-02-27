from django.core.management.base import BaseCommand
from apps.training.models import TrainingModule, TrainingQuestion


class Command(BaseCommand):
    help = 'Seed phishing awareness training modules with bilingual content'

    def handle(self, *args, **options):
        VIDEO_URL = 'https://www.youtube.com/embed/XBkzBrXlle0'

        modules_data = [
            {
                'title': 'Email Phishing Awareness',
                'title_ar': 'التوعية بالتصيد الإلكتروني',
                'description': 'Learn to identify and protect yourself from email phishing attacks targeting Saudi users.',
                'description_ar': 'تعلم كيفية التعرف على هجمات التصيد الإلكتروني وحماية نفسك منها.',
                'category': 'EMAIL_SECURITY',
                'content_type': 'VIDEO',
                'difficulty': 'BEGINNER',
                'video_url': VIDEO_URL,
                'duration_minutes': 15,
                'passing_score': 80,
                'is_active': True,
                'company': None,
                'content_html': '<p>Email phishing is one of the most common cyber threats. Attackers send fraudulent emails that appear to come from trusted sources to steal sensitive information. Learn how to identify red flags such as suspicious sender addresses, urgent language, and malicious links.</p>',
                'content_html_ar': '<p>التصيد الإلكتروني هو أحد أكثر التهديدات السيبرانية شيوعًا. يرسل المهاجمون رسائل بريد إلكتروني احتيالية تبدو وكأنها من مصادر موثوقة لسرقة المعلومات الحساسة. تعلم كيفية التعرف على العلامات التحذيرية مثل عناوين المرسل المشبوهة واللغة العاجلة والروابط الضارة.</p>',
                'questions': [
                    {
                        'question_number': 1,
                        'question_text': 'What is email phishing?',
                        'question_text_ar': 'ما هو التصيد الإلكتروني؟',
                        'options': [
                            'A legitimate email from your bank',
                            'A fraudulent email designed to steal your personal information',
                            'A newsletter subscription email',
                            'An official government notification',
                        ],
                        'options_ar': [
                            'بريد إلكتروني شرعي من بنكك',
                            'بريد إلكتروني احتيالي مصمم لسرقة معلوماتك الشخصية',
                            'بريد اشتراك في نشرة إخبارية',
                            'إشعار حكومي رسمي',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Phishing is a cyberattack that uses fake emails to trick users into revealing sensitive information like passwords and credit card numbers.',
                        'explanation_ar': 'التصيد هو هجوم إلكتروني يستخدم رسائل بريد مزيفة لخداع المستخدمين للكشف عن معلومات حساسة مثل كلمات المرور وأرقام بطاقات الائتمان.',
                    },
                    {
                        'question_number': 2,
                        'question_text': 'Which of the following is a red flag in an email?',
                        'question_text_ar': 'أي من التالي يعتبر علامة تحذير في البريد الإلكتروني؟',
                        'options': [
                            'Email from your manager about a weekly meeting',
                            'Urgent request to verify your Absher account immediately',
                            'Monthly company newsletter',
                            'Calendar invite for team lunch',
                        ],
                        'options_ar': [
                            'بريد من مديرك عن اجتماع أسبوعي',
                            'طلب عاجل للتحقق من حساب أبشر الخاص بك فوراً',
                            'النشرة الإخبارية الشهرية للشركة',
                            'دعوة تقويم لغداء الفريق',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Urgent requests about official accounts like Absher are common phishing tactics. Real government services never email urgent verification requests.',
                        'explanation_ar': 'الطلبات العاجلة المتعلقة بحسابات رسمية مثل أبشر هي أساليب تصيد شائعة. الخدمات الحكومية الحقيقية لا ترسل طلبات تحقق عاجلة عبر البريد الإلكتروني.',
                    },
                    {
                        'question_number': 3,
                        'question_text': 'What should you do when receiving a suspicious email?',
                        'question_text_ar': 'ماذا تفعل عند استلام بريد إلكتروني مشبوه؟',
                        'options': [
                            'Click all links to verify they are safe',
                            'Reply with your personal information to confirm',
                            'Report it to IT and do not click any links',
                            'Forward it to all colleagues as a warning',
                        ],
                        'options_ar': [
                            'انقر على جميع الروابط للتحقق من أنها آمنة',
                            'رد بمعلوماتك الشخصية للتأكيد',
                            'أبلغ قسم تقنية المعلومات ولا تنقر على أي روابط',
                            'أرسله إلى جميع الزملاء كتحذير',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Always report suspicious emails to your IT security team and never click any links or download attachments.',
                        'explanation_ar': 'أبلغ دائمًا فريق أمن تقنية المعلومات عن الرسائل المشبوهة ولا تنقر أبدًا على الروابط أو تحمّل المرفقات.',
                    },
                    {
                        'question_number': 4,
                        'question_text': 'How can you verify if an email is really from Absher?',
                        'question_text_ar': 'كيف يمكنك التحقق من أن البريد الإلكتروني من أبشر فعلاً؟',
                        'options': [
                            'Check if it has the official Absher logo',
                            'Visit absher.com.sa directly instead of clicking links in the email',
                            'Call the phone number mentioned in the email',
                            'Reply asking them to confirm their identity',
                        ],
                        'options_ar': [
                            'تحقق إذا كان يحتوي على شعار أبشر الرسمي',
                            'زر absher.com.sa مباشرةً بدلاً من النقر على روابط البريد',
                            'اتصل برقم الهاتف المذكور في البريد الإلكتروني',
                            'رد طالباً منهم تأكيد هويتهم',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Always navigate to official websites directly by typing the URL in your browser. Never trust links inside emails.',
                        'explanation_ar': 'انتقل دائمًا إلى المواقع الرسمية مباشرةً عن طريق كتابة عنوان URL في متصفحك. لا تثق أبدًا بالروابط داخل رسائل البريد الإلكتروني.',
                    },
                    {
                        'question_number': 5,
                        'question_text': 'What makes a phishing email look convincing?',
                        'question_text_ar': 'ما الذي يجعل بريد التصيد يبدو مقنعاً؟',
                        'options': [
                            'Poor grammar and many spelling mistakes',
                            'Using official logos, creating urgency, and spoofing real email addresses',
                            'Sending from personal Gmail accounts only',
                            'Including too many attachments and images',
                        ],
                        'options_ar': [
                            'قواعد لغة سيئة وأخطاء إملائية كثيرة',
                            'استخدام الشعارات الرسمية وخلق الإلحاح وانتحال عناوين البريد الحقيقية',
                            'الإرسال من حسابات Gmail الشخصية فقط',
                            'تضمين مرفقات وصور كثيرة جداً',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Modern phishing emails look very professional. They copy real logos, create fake urgency, and use email addresses that look similar to real ones.',
                        'explanation_ar': 'رسائل التصيد الحديثة تبدو احترافية جداً. إنها تنسخ الشعارات الحقيقية وتخلق إلحاحاً زائفاً وتستخدم عناوين بريد إلكتروني تشبه العناوين الحقيقية.',
                    },
                ],
            },
            {
                'title': 'SMS Phishing (Smishing) Awareness',
                'title_ar': 'التوعية بالتصيد عبر الرسائل النصية',
                'description': 'Learn to identify and protect yourself from SMS phishing attacks (Smishing) targeting Saudi mobile users.',
                'description_ar': 'تعلم كيفية التعرف على هجمات التصيد عبر الرسائل النصية وحماية نفسك منها.',
                'category': 'MOBILE_SECURITY',
                'content_type': 'VIDEO',
                'difficulty': 'BEGINNER',
                'video_url': VIDEO_URL,
                'duration_minutes': 15,
                'passing_score': 80,
                'is_active': True,
                'company': None,
                'content_html': '<p>Smishing (SMS phishing) uses text messages to trick you into clicking malicious links or revealing personal information. These attacks often impersonate banks, government services like Nafath, or delivery companies like Saudi Post.</p>',
                'content_html_ar': '<p>التصيد عبر الرسائل النصية يستخدم الرسائل القصيرة لخداعك للنقر على روابط ضارة أو الكشف عن معلومات شخصية. غالبًا ما تنتحل هذه الهجمات صفة البنوك أو الخدمات الحكومية مثل نفاذ أو شركات التوصيل مثل البريد السعودي.</p>',
                'questions': [
                    {
                        'question_number': 1,
                        'question_text': 'What is smishing (SMS phishing)?',
                        'question_text_ar': 'ما هو التصيد عبر الرسائل النصية (Smishing)؟',
                        'options': [
                            'Phishing attacks conducted via email',
                            'Phishing attacks conducted via SMS text messages',
                            'Phishing attacks conducted via phone calls',
                            'Phishing attacks via social media messages',
                        ],
                        'options_ar': [
                            'هجمات التصيد عبر البريد الإلكتروني',
                            'هجمات التصيد عبر الرسائل النصية القصيرة',
                            'هجمات التصيد عبر المكالمات الهاتفية',
                            'هجمات التصيد عبر رسائل وسائل التواصل الاجتماعي',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Smishing is phishing conducted specifically through SMS text messages to trick users into revealing sensitive information.',
                        'explanation_ar': 'التصيد النصي هو هجوم يتم عبر رسائل SMS لخداع المستخدمين للكشف عن معلومات حساسة.',
                    },
                    {
                        'question_number': 2,
                        'question_text': 'Which SMS message is most likely a smishing attempt?',
                        'question_text_ar': 'أي رسالة نصية على الأرجح محاولة تصيد؟',
                        'options': [
                            'Your OTP code from Nafath is: 123456. Do not share it.',
                            'Your Nafath account is suspended! Click here immediately to restore: http://nafath-verify.net',
                            'Your appointment at the clinic is confirmed for tomorrow at 10am',
                            'Your SADAD bill is due on the 15th of this month',
                        ],
                        'options_ar': [
                            'رمز OTP الخاص بك من نفاذ هو: 123456. لا تشاركه.',
                            'تم تعليق حساب نفاذ! انقر هنا فوراً للاستعادة: http://nafath-verify.net',
                            'تم تأكيد موعدك في العيادة غداً الساعة 10 صباحاً',
                            'فاتورة سداد مستحقة في الخامس عشر من هذا الشهر',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'The fake link "nafath-verify.net" is a clear sign of smishing. Official services use their verified domain names only.',
                        'explanation_ar': 'الرابط المزيف "nafath-verify.net" هو علامة واضحة على التصيد النصي. الخدمات الرسمية تستخدم أسماء نطاقها المعتمدة فقط.',
                    },
                    {
                        'question_number': 3,
                        'question_text': 'What should you do when you receive a suspicious SMS with a link?',
                        'question_text_ar': 'ماذا تفعل عند استلام رسالة نصية مشبوهة تحتوي على رابط؟',
                        'options': [
                            'Click the link quickly before it expires',
                            'Forward it to friends to warn them',
                            'Delete the message and report it to CITC or your IT team',
                            'Reply STOP to unsubscribe from the messages',
                        ],
                        'options_ar': [
                            'انقر على الرابط بسرعة قبل انتهاء صلاحيته',
                            'أرسله للأصدقاء لتحذيرهم',
                            'احذف الرسالة وأبلغ عنها لهيئة الاتصالات أو فريق تقنية المعلومات',
                            'رد بـ STOP لإلغاء الاشتراك من الرسائل',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Delete suspicious messages immediately and report to CITC. Never click unknown links in SMS.',
                        'explanation_ar': 'احذف الرسائل المشبوهة فوراً وأبلغ هيئة الاتصالات. لا تنقر أبداً على روابط مجهولة في الرسائل النصية.',
                    },
                    {
                        'question_number': 4,
                        'question_text': 'You receive an SMS claiming your Saudi Post package needs customs fees. What do you do?',
                        'question_text_ar': 'استلمت رسالة نصية تدّعي أن طردك من البريد السعودي يحتاج رسوم جمركية. ماذا تفعل؟',
                        'options': [
                            'Pay immediately using the link in the SMS',
                            'Call the number in the SMS to confirm',
                            'Visit the official Saudi Post website or app directly to check',
                            'Ignore it as packages never need customs fees',
                        ],
                        'options_ar': [
                            'ادفع فوراً باستخدام الرابط في الرسالة',
                            'اتصل بالرقم في الرسالة للتأكيد',
                            'زر موقع البريد السعودي الرسمي أو التطبيق مباشرةً للتحقق',
                            'تجاهله لأن الطرود لا تحتاج رسوماً جمركية',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Always verify by visiting the official Saudi Post website (sp.com.sa) directly, not through SMS links.',
                        'explanation_ar': 'تحقق دائماً بزيارة موقع البريد السعودي الرسمي (sp.com.sa) مباشرةً، وليس عبر روابط الرسائل.',
                    },
                    {
                        'question_number': 5,
                        'question_text': 'What is the goal of a smishing attack?',
                        'question_text_ar': 'ما هو الهدف من هجوم التصيد النصي؟',
                        'options': [
                            'To send you promotional offers from companies',
                            'To steal personal information, credentials, or money',
                            'To update your phone software remotely',
                            'To verify your identity for security purposes',
                        ],
                        'options_ar': [
                            'لإرسال عروض ترويجية من الشركات',
                            'لسرقة المعلومات الشخصية أو بيانات الاعتماد أو المال',
                            'لتحديث برنامج هاتفك عن بُعد',
                            'للتحقق من هويتك لأغراض أمنية',
                        ],
                        'correct_answer_index': 1,
                        'explanation': 'Smishing attacks always aim to steal credentials, financial information, or install malware on your device.',
                        'explanation_ar': 'تهدف هجمات التصيد النصي دائماً إلى سرقة بيانات الاعتماد أو المعلومات المالية أو تثبيت برامج ضارة على جهازك.',
                    },
                ],
            },
            {
                'title': 'Voice Phishing (Vishing) Awareness',
                'title_ar': 'التوعية بالتصيد الصوتي',
                'description': 'Learn to identify and protect yourself from voice call phishing attacks (Vishing) targeting Saudi residents.',
                'description_ar': 'تعلم كيفية التعرف على هجمات التصيد عبر المكالمات الصوتية وحماية نفسك منها.',
                'category': 'SOCIAL_ENGINEERING',
                'content_type': 'VIDEO',
                'difficulty': 'BEGINNER',
                'video_url': VIDEO_URL,
                'duration_minutes': 15,
                'passing_score': 80,
                'is_active': True,
                'company': None,
                'content_html': '<p>Vishing (voice phishing) uses phone calls to trick you into revealing personal or financial information. Attackers may impersonate banks, government agencies like the Ministry of Interior, or other trusted organizations.</p>',
                'content_html_ar': '<p>التصيد الصوتي يستخدم المكالمات الهاتفية لخداعك للكشف عن معلومات شخصية أو مالية. قد ينتحل المهاجمون صفة البنوك أو الجهات الحكومية مثل وزارة الداخلية أو منظمات موثوقة أخرى.</p>',
                'questions': [
                    {
                        'question_number': 1,
                        'question_text': 'What is vishing (voice phishing)?',
                        'question_text_ar': 'ما هو التصيد الصوتي (Vishing)؟',
                        'options': [
                            'Phishing via email messages',
                            'Phishing via SMS text messages',
                            'Phishing via voice phone calls',
                            'Phishing via video conferencing',
                        ],
                        'options_ar': [
                            'التصيد عبر رسائل البريد الإلكتروني',
                            'التصيد عبر الرسائل النصية',
                            'التصيد عبر المكالمات الهاتفية الصوتية',
                            'التصيد عبر مؤتمرات الفيديو',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Vishing uses voice calls (phone calls) to trick victims into revealing sensitive information or transferring money.',
                        'explanation_ar': 'يستخدم التصيد الصوتي المكالمات الهاتفية لخداع الضحايا للكشف عن معلومات حساسة أو تحويل الأموال.',
                    },
                    {
                        'question_number': 2,
                        'question_text': 'Someone calls claiming to be from your bank asking for your PIN and OTP. What do you do?',
                        'question_text_ar': 'اتصل بك شخص يدّعي أنه من بنكك ويطلب رقم PIN ورمز OTP الخاص بك. ماذا تفعل؟',
                        'options': [
                            'Provide the information since they called you',
                            'Give only the last 4 digits of your card',
                            'Hang up immediately and call the official bank number on the back of your card',
                            'Ask them to send an email to verify first',
                        ],
                        'options_ar': [
                            'أعطه المعلومات لأنه هو من اتصل',
                            'أعط الأرقام الأربعة الأخيرة من بطاقتك فقط',
                            'أغلق الخط فوراً واتصل برقم البنك الرسمي المدوّن على ظهر بطاقتك',
                            'اطلب منهم إرسال بريد إلكتروني للتحقق أولاً',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Banks NEVER ask for PINs, passwords or OTPs over the phone. Always hang up and call back on the official number.',
                        'explanation_ar': 'البنوك لا تطلب أبداً أرقام PIN أو كلمات المرور أو رموز OTP عبر الهاتف. أغلق دائماً واتصل على الرقم الرسمي.',
                    },
                    {
                        'question_number': 3,
                        'question_text': 'A caller claims to be from the Ministry of Interior and says you have a legal issue. What should you do?',
                        'question_text_ar': 'يدّعي متصل أنه من وزارة الداخلية ويقول إن لديك مشكلة قانونية. ماذا تفعل؟',
                        'options': [
                            'Provide your national ID number to verify your identity',
                            'Pay any fines they mention immediately to avoid arrest',
                            'Hang up and verify by calling the official ministry number or visiting Absher',
                            'Stay on the line and cooperate to resolve the issue quickly',
                        ],
                        'options_ar': [
                            'أعطه رقم هويتك الوطنية للتحقق من هويتك',
                            'ادفع أي غرامات يذكرونها فوراً لتجنب الاعتقال',
                            'أغلق الخط وتحقق بالاتصال برقم الوزارة الرسمي أو زيارة أبشر',
                            'ابق على الخط وتعاون لحل المشكلة بسرعة',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Government ministries never call to demand immediate payment or personal information. Always verify through official channels like Absher.',
                        'explanation_ar': 'الوزارات الحكومية لا تتصل أبداً لطلب دفع فوري أو معلومات شخصية. تحقق دائماً عبر القنوات الرسمية مثل أبشر.',
                    },
                    {
                        'question_number': 4,
                        'question_text': 'What information should you NEVER share over a phone call?',
                        'question_text_ar': 'ما المعلومات التي يجب ألا تشاركها أبداً عبر مكالمة هاتفية؟',
                        'options': [
                            'Your first and last name',
                            'Your general work location',
                            'OTP codes, bank PINs, passwords, or full National ID details',
                            'Your company name',
                        ],
                        'options_ar': [
                            'اسمك الأول والأخير',
                            'موقع عملك العام',
                            'رموز OTP وأرقام PIN البنكية وكلمات المرور وتفاصيل الهوية الوطنية الكاملة',
                            'اسم شركتك',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Never share OTPs, PINs, passwords, or complete National ID details over any phone call regardless of who is asking.',
                        'explanation_ar': 'لا تشارك أبداً رموز OTP أو أرقام PIN أو كلمات المرور أو تفاصيل الهوية الوطنية الكاملة في أي مكالمة هاتفية.',
                    },
                    {
                        'question_number': 5,
                        'question_text': 'Which is a common vishing tactic used against Saudi residents?',
                        'question_text_ar': 'ما هو أسلوب التصيد الصوتي الشائع المستخدم ضد المقيمين في السعودية؟',
                        'options': [
                            'Offering you a free Hajj or Umrah package',
                            'Asking about your preferred banking hours',
                            'Claiming your Absher account or Iqama has a problem requiring urgent payment',
                            'Offering to help you with a government form',
                        ],
                        'options_ar': [
                            'تقديم باقة حج أو عمرة مجانية لك',
                            'السؤال عن ساعات البنك المفضلة لديك',
                            'ادعاء أن حساب أبشر أو إقامتك بها مشكلة تستوجب دفعاً عاجلاً',
                            'تقديم المساعدة في استمارة حكومية',
                        ],
                        'correct_answer_index': 2,
                        'explanation': 'Threatening residents about Absher, Iqama issues, or demanding urgent payments is the most common vishing tactic in Saudi Arabia.',
                        'explanation_ar': 'التهديد بشأن أبشر أو مشاكل الإقامة أو المطالبة بمدفوعات عاجلة هو أكثر أساليب التصيد الصوتي شيوعاً في المملكة العربية السعودية.',
                    },
                ],
            },
        ]

        for module_data in modules_data:
            questions_data = module_data.pop('questions')

            module, created = TrainingModule.objects.update_or_create(
                title=module_data['title'],
                defaults=module_data,
            )

            status_label = 'Created' if created else 'Updated'
            self.stdout.write(f'{status_label}: {module.title}')

            # Clear and recreate questions for idempotency
            TrainingQuestion.objects.filter(module=module).delete()

            for q_data in questions_data:
                TrainingQuestion.objects.create(module=module, **q_data)

            self.stdout.write(f'  + {len(questions_data)} bilingual questions added')

        self.stdout.write(
            self.style.SUCCESS('\nTraining modules seeded successfully!')
        )
