import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ups", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CallClosure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("work_order", models.CharField(max_length=100, verbose_name="Work Order")),
                ("ups_model", models.CharField(max_length=100, verbose_name="UPS Model")),
                ("serial_number", models.CharField(max_length=100, verbose_name="UPS Serial Number")),
                ("type_of_call", models.CharField(choices=[("WARRANTY", "Warranty"), ("AMC", "AMC"), ("OUT_OF_WARRANTY", "Out of Warranty")], max_length=20, verbose_name="Type of Call")),
                ("root_cause", models.TextField(verbose_name="Root Cause")),
                ("action_taken", models.TextField(verbose_name="Action Taken")),
                ("voltage", models.CharField(max_length=50, verbose_name="Voltage")),
                ("earthing", models.CharField(max_length=50, verbose_name="Earthing")),
                ("part_replaced", models.BooleanField(default=False, verbose_name="Part Replaced")),
                ("indent_required", models.BooleanField(default=False, verbose_name="Indent Required")),
                ("defective_part_photo", models.ImageField(blank=True, null=True, upload_to="closure/defective/", verbose_name="Defective Part Photo")),
                ("new_part_photo", models.ImageField(blank=True, null=True, upload_to="closure/new/", verbose_name="New Part Photo")),
                ("customer_signature_name", models.CharField(max_length=150, verbose_name="Customer Name")),
                ("customer_signature", models.TextField(verbose_name="Customer Signature (Data URL)")),
                ("engineer_remarks", models.TextField(blank=True, verbose_name="Engineer Remarks")),
                ("site_photos", models.ImageField(blank=True, null=True, upload_to="closure/site/", verbose_name="Site Photos")),
                ("completion_date", models.DateField(verbose_name="Completion Date")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("service_request", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="closure", to="ups.servicerequest", verbose_name="Service Request")),
            ],
            options={
                "verbose_name": "Call Closure",
                "verbose_name_plural": "Call Closures",
            },
        ),
    ]
