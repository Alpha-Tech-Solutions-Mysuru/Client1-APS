from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ups", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicerequest",
            name="type_of_call",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="servicerequest",
            name="work_order_number",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="address",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="kva",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="pincode",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="problem",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="state",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="servicerequest",
            name="ups_make",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
