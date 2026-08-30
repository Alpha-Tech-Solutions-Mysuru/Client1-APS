from django.db import migrations


def sync_superuser_roles(apps, schema_editor):

    User = apps.get_model("accounts", "User")

    User.objects.filter(is_superuser=True).update(
        role="ADMIN",
        is_staff=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_visible_password"),
    ]

    operations = [
        migrations.RunPython(sync_superuser_roles, migrations.RunPython.noop),
    ]
