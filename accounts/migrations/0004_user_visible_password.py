from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_mobile_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="visible_password",
            field=models.CharField(
                blank=True,
                max_length=128,
                null=True,
                verbose_name="Visible Password",
            ),
        ),
    ]
