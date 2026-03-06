from rest_framework import serializers
from .models import EmailTemplate, QuizQuestion


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model."""

    is_phishing = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'campaign', 'sender_name', 'sender_email', 'subject',
            'body', 'has_attachments', 'attachment_names', 'links',
            'email_type', 'category', 'difficulty', 'is_phishing',
            'is_ai_generated', 'ai_model_used', 'generation_prompt',
            'red_flags', 'explanation', 'explanation_ar', 'language',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating email templates."""

    class Meta:
        model = EmailTemplate
        fields = [
            'campaign', 'sender_name', 'sender_email', 'subject', 'body',
            'has_attachments', 'attachment_names', 'links', 'email_type',
            'category', 'difficulty', 'is_ai_generated', 'ai_model_used',
            'generation_prompt', 'red_flags', 'explanation',
            'explanation_ar', 'language'
        ]

    def create(self, validated_data):
        """Create email template and set created_by from request user."""
        if 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AIEmailGenerationRequestSerializer(serializers.Serializer):
    """Serializer for AI email generation request."""

    campaign_id = serializers.IntegerField()
    num_phishing_emails = serializers.IntegerField(min_value=1, max_value=40)
    num_legitimate_emails = serializers.IntegerField(min_value=1, max_value=40)
    language = serializers.ChoiceField(choices=['en', 'ar'], default='en')
    difficulty_distribution = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        help_text="Distribution of difficulty levels: {'EASY': 3, 'MEDIUM': 4, 'HARD': 3}"
    )
    phishing_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of phishing categories to generate"
    )

    def validate(self, attrs):
        """Validate the generation request."""
        difficulty_dist = attrs.get('difficulty_distribution', {})
        if difficulty_dist:
            total = sum(difficulty_dist.values())
            if total != attrs['num_phishing_emails']:
                raise serializers.ValidationError({
                    "difficulty_distribution": f"Difficulty distribution total ({total}) must match num_phishing_emails ({attrs['num_phishing_emails']})"
                })
        return attrs


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for QuizQuestion model."""

    email_subject = serializers.CharField(source='email_template.subject', read_only=True)
    correct_answer = serializers.CharField(read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'quiz', 'email_template', 'email_subject',
            'question_number', 'answer', 'is_correct', 'correct_answer',
            'confidence_level', 'time_spent_seconds', 'answered_at',
            'requires_training', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_correct', 'correct_answer', 'created_at', 'updated_at']
