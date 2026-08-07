from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('routines', '0002_weeklyroutineitem_deleted_at'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='routineoccurrence',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        status='pending',
                        completed_at__isnull=True,
                        skipped_at__isnull=True,
                    )
                    | models.Q(
                        status='completed',
                        completed_at__isnull=False,
                        skipped_at__isnull=True,
                    )
                    | models.Q(
                        status='skipped',
                        completed_at__isnull=True,
                        skipped_at__isnull=False,
                    )
                ),
                name='routine_occ_status_timestamps',
            ),
        ),
    ]
