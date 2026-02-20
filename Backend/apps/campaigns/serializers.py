from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Campaign, Quiz, QuizResult
from apps.assessments.models import EmailTemplate, QuizQuestion

User = get_user_model()


class CampaignListSerializer(serializers.ModelSerializer):
    """Serializer for Campaign list view."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    num_phishing_emails = serializers.IntegerField(read_only=True)
    num_legitimate_emails = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'name_ar', 'company', 'company_name',
            'created_by', 'created_by_name', 'status', 'num_emails',
            'phishing_ratio', 'num_phishing_emails', 'num_legitimate_emails',
            'start_date', 'end_date', 'is_active', 'total_participants',
            'completed_participants', 'completion_rate', 'average_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_participants', 'completed_participants', 'average_score']


class CampaignDetailSerializer(serializers.ModelSerializer):
    """Serializer for Campaign detail view with full information."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    num_phishing_emails = serializers.IntegerField(read_only=True)
    num_legitimate_emails = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'name_ar', 'description', 'description_ar',
            'company', 'company_name', 'created_by', 'created_by_name',
            'num_emails', 'phishing_ratio', 'num_phishing_emails',
            'num_legitimate_emails', 'status', 'start_date', 'end_date',
            'is_active', 'total_participants', 'completed_participants',
            'completion_rate', 'average_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_participants', 'completed_participants', 'average_score']


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new campaign."""

    class Meta:
        model = Campaign
        fields = [
            'name', 'name_ar', 'description', 'description_ar',
            'company', 'num_emails', 'phishing_ratio', 'status',
            'start_date', 'end_date'
        ]

    def validate_phishing_ratio(self, value):
        """Validate phishing ratio is within acceptable range."""
        if value < 0.2 or value > 0.8:
            raise serializers.ValidationError("Phishing ratio must be between 0.2 and 0.8")
        return value

    def validate_num_emails(self, value):
        """Validate number of emails is within acceptable range."""
        if value < 5 or value > 50:
            raise serializers.ValidationError("Number of emails must be between 5 and 50")
        return value

    def validate(self, attrs):
        """Validate campaign dates."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date:
            if end_date <= start_date:
                raise serializers.ValidationError({
                    "end_date": "End date must be after start date"
                })

        return attrs

    def create(self, validated_data):
        """Create campaign and set created_by from request user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class QuizQuestionSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for quiz questions without revealing answers."""

    email_subject = serializers.CharField(source='email_template.subject', read_only=True)
    email_sender_name = serializers.CharField(source='email_template.sender_name', read_only=True)
    email_sender_email = serializers.CharField(source='email_template.sender_email', read_only=True)
    email_body = serializers.CharField(source='email_template.body', read_only=True)
    has_attachments = serializers.BooleanField(source='email_template.has_attachments', read_only=True)
    attachment_names = serializers.JSONField(source='email_template.attachment_names', read_only=True)
    links = serializers.JSONField(source='email_template.links', read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_number', 'email_subject', 'email_sender_name',
            'email_sender_email', 'email_body', 'has_attachments',
            'attachment_names', 'links', 'answer', 'confidence_level'
        ]
        read_only_fields = ['id', 'question_number']


class QuizQuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for quiz questions with answers (for results)."""

    email_template = serializers.SerializerMethodField()
    correct_answer = serializers.CharField(read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_number', 'email_template', 'answer',
            'is_correct', 'correct_answer', 'confidence_level',
            'time_spent_seconds', 'answered_at', 'requires_training'
        ]
        read_only_fields = ['id', 'question_number', 'is_correct', 'correct_answer']

    def get_email_template(self, obj):
        """Return email template with red flags and explanation."""
        return {
            'subject': obj.email_template.subject,
            'sender_name': obj.email_template.sender_name,
            'sender_email': obj.email_template.sender_email,
            'body': obj.email_template.body,
            'email_type': obj.email_template.email_type,
            'category': obj.email_template.category,
            'difficulty': obj.email_template.difficulty,
            'red_flags': obj.email_template.red_flags,
            'explanation': obj.email_template.explanation,
            'explanation_ar': obj.email_template.explanation_ar,
        }


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for Quiz model."""

    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    time_taken = serializers.SerializerMethodField(read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    answered_questions = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'campaign', 'campaign_name', 'employee', 'employee_name',
            'status', 'current_question_index', 'total_questions',
            'answered_questions', 'progress_percentage', 'started_at',
            'completed_at', 'time_taken', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def get_time_taken(self, obj):
        """Return time taken as total seconds."""
        time_taken = obj.time_taken
        if time_taken:
            return time_taken.total_seconds()
        return None


class QuizResultSerializer(serializers.ModelSerializer):
    """Serializer for QuizResult model."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    accuracy = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    phishing_detection_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = QuizResult
        fields = [
            'id', 'quiz', 'employee', 'employee_name', 'campaign',
            'campaign_name', 'total_questions', 'correct_answers',
            'incorrect_answers', 'score', 'accuracy',
            'phishing_emails_identified', 'phishing_emails_missed',
            'false_positives', 'phishing_detection_rate',
            'time_taken_seconds', 'average_time_per_question',
            'risk_level', 'passed', 'completed_at'
        ]
        read_only_fields = ['id', 'completed_at']


class AnswerQuestionSerializer(serializers.Serializer):
    """Serializer for submitting an answer to a quiz question."""

    answer = serializers.ChoiceField(choices=['PHISHING', 'LEGITIMATE'])
    confidence_level = serializers.IntegerField(min_value=1, max_value=5, required=False)
    time_spent_seconds = serializers.IntegerField(min_value=0, required=False)
