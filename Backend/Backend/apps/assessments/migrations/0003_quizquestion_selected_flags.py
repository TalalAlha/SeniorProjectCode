from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizquestion',
            name='selected_flags',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of red flag IDs the employee selected when answering PHISHING',
                verbose_name='selected red flags',
            ),
        ),
    ]
