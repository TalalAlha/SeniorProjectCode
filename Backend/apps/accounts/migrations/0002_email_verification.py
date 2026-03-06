import uuid
import django.utils.timezone
from django.db import migrations, models


def populate_verification_tokens(apps, schema_editor):
    """Assign a unique UUID to every existing user row."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        user.verification_token = uuid.uuid4()
        user.save(update_fields=['verification_token'])


def mark_existing_users_verified(apps, schema_editor):
    """
    Users who existed before email verification was introduced are
    treated as already verified so they are not locked out.
    """
    User = apps.get_model('accounts', 'User')
    User.objects.all().update(is_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Step 1 — add token column as nullable (no unique constraint yet)
        migrations.AddField(
            model_name='user',
            name='verification_token',
            field=models.UUIDField(null=True, blank=True),
        ),

        # Step 2 — populate unique UUIDs for all existing rows
        migrations.RunPython(populate_verification_tokens, migrations.RunPython.noop),

        # Step 3 — make the column non-nullable and unique
        migrations.AlterField(
            model_name='user',
            name='verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),

        # Step 4 — add token creation timestamp
        migrations.AddField(
            model_name='user',
            name='verification_token_created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),

        # Step 5 — mark all pre-existing users as verified
        migrations.RunPython(mark_existing_users_verified, migrations.RunPython.noop),
    ]
