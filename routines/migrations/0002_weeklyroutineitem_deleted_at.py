from django.db import migrations, models


def normalize_daily_habits(apps, schema_editor):
    routine_item = apps.get_model('routines', 'WeeklyRoutineItem')
    for item in routine_item.objects.all().iterator():
        item.starts_on = item.starts_on.replace(day=1)
        item.weekdays = list(range(7))
        item.save(update_fields=('starts_on', 'weekdays'))


class Migration(migrations.Migration):
    dependencies = [
        ('routines', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklyroutineitem',
            name='deleted_at',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name='excluída em',
            ),
        ),
        migrations.RunPython(normalize_daily_habits, migrations.RunPython.noop),
    ]
