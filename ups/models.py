from django.db import models

from accounts.models import User


class ServiceRequest(models.Model):

    CALL_TYPE_CHOICES = [
        ("WARRANTY", "Warranty"),
        ("AMC", "AMC"),
        ("OUT_OF_WARRANTY", "Out of Warranty"),
    ]

    work_order_number = models.CharField(
        max_length=100,
        blank=True,
    )

    client_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    customer_name = models.CharField(
        max_length=150,
    )

    company_name = models.CharField(
        max_length=150,
        blank=True,
    )

    mobile_number = models.CharField(
        max_length=15,
    )

    type_of_call = models.CharField(
        max_length=50,
        blank=True,
        choices=CALL_TYPE_CHOICES,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    ups_make = models.CharField(
        max_length=100,
        blank=True,
    )

    ups_model = models.CharField(
        max_length=100,
    )

    serial_number = models.CharField(
        max_length=100,
    )

    kva = models.CharField(
        max_length=30,
        blank=True,
    )

    battery_details = models.CharField(
        max_length=150,
        blank=True,
    )

    problem = models.TextField(
        blank=True,
    )

    engineer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_requests",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "-created_at",
        ]

        verbose_name = "Service Request"

        verbose_name_plural = "Service Requests"

    def __str__(self):

        return self.client_id


class EngineerVisitWorkflow(models.Model):

    PART_DECISION_CHOICES = [
        ("AVAILABLE", "Part Available"),
        ("NOT_AVAILABLE", "Part Not Available"),
    ]

    COMPLAINT_MATCH_CHOICES = [
        ("MATCHED", "Matched"),
        ("MISMATCHED", "Mismatched"),
    ]

    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="workflow",
    )

    step_1_customer_contacted = models.BooleanField(
        default=False,
    )

    step_1_problem_confirmed = models.BooleanField(
        default=False,
    )

    step_1_location_confirmed = models.BooleanField(
        default=False,
    )

    step_1_visit_schedule_confirmed = models.BooleanField(
        default=False,
    )

    step_1_problem_confirmation_notes = models.TextField(
        blank=True,
    )

    step_1_location_confirmation_notes = models.TextField(
        blank=True,
    )

    step_1_visit_schedule_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_1_remarks = models.TextField(
        blank=True,
    )

    step_1_completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_2_model_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_2_serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_2_equipment_photo = models.ImageField(
        upload_to="workflow/step2/equipment/",
        blank=True,
        null=True,
    )

    step_2_model_label_photo = models.ImageField(
        upload_to="workflow/step2/model-label/",
        blank=True,
        null=True,
    )

    step_2_serial_label_photo = models.ImageField(
        upload_to="workflow/step2/serial-label/",
        blank=True,
        null=True,
    )

    step_2_complaint_match_status = models.CharField(
        max_length=20,
        choices=COMPLAINT_MATCH_CHOICES,
        blank=True,
    )

    step_2_completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_3_problem_analysis = models.TextField(
        blank=True,
    )

    step_3_system_data = models.TextField(
        blank=True,
    )

    step_3_category_data = models.JSONField(
        default=list,
        blank=True,
    )

    step_3_additional_observations = models.TextField(
        blank=True,
    )

    step_3_supporting_photo = models.ImageField(
        upload_to="workflow/step3/supporting/",
        blank=True,
        null=True,
    )

    step_3_completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_4_part_decision = models.CharField(
        max_length=20,
        choices=PART_DECISION_CHOICES,
        blank=True,
    )

    step_4_replacement_required = models.BooleanField(
        default=False,
    )

    step_4_required_part_details = models.TextField(
        blank=True,
    )

    step_4_indent_details = models.TextField(
        blank=True,
    )

    step_4_defective_part_photo = models.ImageField(
        upload_to="workflow/step4/defective/",
        blank=True,
        null=True,
    )

    step_4_remarks = models.TextField(
        blank=True,
    )

    step_4_completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_5_new_part_name = models.CharField(
        max_length=150,
        blank=True,
    )

    step_5_new_part_model_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_5_new_part_serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_5_defective_part_model_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_5_defective_part_serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    step_5_replacement_date_time = models.DateTimeField(
        blank=True,
        null=True,
    )

    step_5_installed_part_photo = models.ImageField(
        upload_to="workflow/step5/installed/",
        blank=True,
        null=True,
    )

    step_5_defective_part_photo = models.ImageField(
        upload_to="workflow/step5/defective/",
        blank=True,
        null=True,
    )

    step_5_completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        verbose_name = "Engineer Visit Workflow"

        verbose_name_plural = "Engineer Visit Workflows"

    def __str__(self):

        return f"Workflow for {self.service_request.client_id}"

    def _get_image_group(self, image_type):

        image_map = {
            "DEFECTIVE": [
                self.step_4_defective_part_photo,
                self.step_5_defective_part_photo,
            ],
            "REPLACED": [
                self.step_5_installed_part_photo,
            ],
            "MODEL_SERIAL": [
                self.step_2_model_label_photo,
            ],
        }
        images = []
        seen_names = set()

        for image_field in image_map.get(image_type, []):
            if image_field and getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append(image_field)
                seen_names.add(image_field.name)

        for item in self.additional_images.filter(image_type=image_type).order_by("created_at", "pk"):
            if item.image and getattr(item.image, "name", "") and item.image.name not in seen_names:
                images.append(item.image)
                seen_names.add(item.image.name)

        return images

    def get_defective_part_images(self):

        return self._get_image_group("DEFECTIVE")

    def get_replaced_part_images(self):

        return self._get_image_group("REPLACED")

    def get_model_serial_images(self):

        return self._get_image_group("MODEL_SERIAL")


class WorkflowAdditionalImage(models.Model):

    IMAGE_TYPE_CHOICES = [
        ("DEFECTIVE", "Defective Part"),
        ("REPLACED", "Replaced Part"),
        ("MODEL_SERIAL", "Model/Serial Label"),
    ]

    workflow = models.ForeignKey(
        EngineerVisitWorkflow,
        on_delete=models.CASCADE,
        related_name="additional_images",
    )

    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
    )

    image = models.ImageField(
        upload_to="workflow/additional/",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "Workflow Additional Image"

        verbose_name_plural = "Workflow Additional Images"

    def __str__(self):

        return f"{self.get_image_type_display()} - {self.workflow.service_request.client_id}"


class CallClosure(models.Model):

    APPROVAL_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
    ]

    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="closure",
        verbose_name="Service Request",
    )

    work_order = models.CharField(
        max_length=100,
        verbose_name="Work Order",
    )

    ups_model = models.CharField(
        max_length=100,
        verbose_name="UPS Model",
    )

    serial_number = models.CharField(
        max_length=100,
        verbose_name="UPS Serial Number",
    )

    CALL_TYPE_CHOICES = [
        ("WARRANTY", "Warranty"),
        ("AMC", "AMC"),
        ("OUT_OF_WARRANTY", "Out of Warranty"),
    ]

    type_of_call = models.CharField(
        max_length=20,
        choices=CALL_TYPE_CHOICES,
        verbose_name="Type of Call",
    )

    root_cause = models.TextField(
        verbose_name="Root Cause",
    )

    action_taken = models.TextField(
        verbose_name="Action Taken",
    )

    voltage = models.CharField(
        max_length=50,
        verbose_name="Voltage",
    )

    earthing = models.CharField(
        max_length=50,
        verbose_name="Earthing",
    )

    part_replaced = models.BooleanField(
        default=False,
        verbose_name="Part Replaced",
    )

    indent_required = models.BooleanField(
        default=False,
        verbose_name="Indent Required",
    )

    defective_part_photo = models.ImageField(
        upload_to="closure/defective/",
        blank=True,
        null=True,
        verbose_name="Defective Part Photo",
    )

    new_part_photo = models.ImageField(
        upload_to="closure/new/",
        blank=True,
        null=True,
        verbose_name="New Part Photo",
    )

    customer_signature_name = models.CharField(
        max_length=150,
        verbose_name="Customer Name",
    )

    customer_signature = models.TextField(
        verbose_name="Customer Signature (Data URL)",
        blank=True,
    )

    engineer_remarks = models.TextField(
        blank=True,
        verbose_name="Engineer Remarks",
    )

    site_photos = models.ImageField(
        upload_to="closure/site/",
        blank=True,
        null=True,
        verbose_name="Site Photos",
    )

    completion_date = models.DateField(
        verbose_name="Completion Date",
    )

    customer_mobile_number = models.CharField(
        max_length=15,
        blank=True,
    )

    customer_email = models.EmailField(
        blank=True,
    )

    out_of_scope_observations = models.TextField(
        blank=True,
    )

    out_of_scope_reported = models.BooleanField(
        default=False,
    )

    ups_operational_verified = models.BooleanField(
        default=False,
    )

    working_condition_demonstrated = models.BooleanField(
        default=False,
    )

    closure_recorded_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default="PENDING",
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        verbose_name = "Call Closure"

        verbose_name_plural = "Call Closures"

    def __str__(self):

        return f"Closure for {self.service_request.client_id}"

    def get_installation_images(self):
        images = []
        seen_names = set()
        if self.site_photos and getattr(self.site_photos, "name", ""):
            images.append(self.site_photos)
            seen_names.add(self.site_photos.name)
        for item in self.additional_images.all().order_by("created_at", "pk"):
            if item.image and getattr(item.image, "name", "") and item.image.name not in seen_names:
                images.append(item.image)
                seen_names.add(item.image.name)
        return images


class ClosureAdditionalImage(models.Model):

    closure = models.ForeignKey(
        CallClosure,
        on_delete=models.CASCADE,
        related_name="additional_images",
    )

    image = models.ImageField(
        upload_to="closure/additional/",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "Closure Additional Image"

        verbose_name_plural = "Closure Additional Images"

    def __str__(self):

        return f"Closure Image for {self.closure.service_request.client_id}"
