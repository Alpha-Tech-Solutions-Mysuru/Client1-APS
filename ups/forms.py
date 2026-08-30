import json

from django import forms
from django.utils import timezone

from accounts.models import User
from accounts.models import UserRole

from .models import ServiceRequest, CallClosure, EngineerVisitWorkflow, WorkflowAdditionalImage


class MultiFileInput(forms.ClearableFileInput):

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):

    widget = MultiFileInput

    def clean(self, data, initial=None):

        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data if item]

        return single_file_clean(data, initial)


class ServiceRequestForm(forms.ModelForm):

    TYPE_OF_CALL_CHOICES = [
        ("", "Select Call Type"),
        ("WARRANTY", "Warranty"),
        ("AMC", "AMC"),
        ("OUT_OF_WARRANTY", "Out of Warranty"),
    ]

    class Meta:

        model = ServiceRequest

        fields = [
            "client_id",
            "work_order_number",
            "customer_name",
            "mobile_number",
            "type_of_call",
            "email",
            "address",
            "ups_model",
            "serial_number",
            "engineer",
        ]

        widgets = {

            "client_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Case ID",
            }),

            "work_order_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Work Order (e.g. WO-1001)",
            }),

            "customer_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter customer name",
            }),

            "mobile_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number",
            }),

            "type_of_call": forms.Select(attrs={
                "class": "form-select",
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address (Optional)",
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter customer address",
            }),

            "ups_model": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Model details (e.g. APC 5KVA)",
            }),

            "serial_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Serial Number",
            }),

            "engineer": forms.Select(attrs={
                "class": "form-select",
            }),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["engineer"].queryset = User.objects.filter(
            role=UserRole.ENGINEER,
            is_active=True,
        ).order_by(
            "first_name",
            "username",
        )

        self.fields["engineer"].empty_label = "Select Engineer"
        self.fields["type_of_call"].choices = self.TYPE_OF_CALL_CHOICES
        self.fields["client_id"].required = True
        self.fields["work_order_number"].required = True
        self.fields["type_of_call"].required = True
    
    def clean_client_id(self):
        client_id = self.cleaned_data["client_id"].strip()

        if not client_id:
            raise forms.ValidationError("Case ID is required.")

        return client_id

    def clean_mobile_number(self):

        mobile = self.cleaned_data["mobile_number"].strip()

        import re
        if not re.match(r"^\d{5} \d{5}$", mobile):

            raise forms.ValidationError(
                "Mobile number must follow the format XXXXX XXXXX (5 digits, space, 5 digits)."
            )

        return mobile


class CallClosureForm(forms.ModelForm):
        model = CallClosure

        fields = [
            "work_order",
            "ups_model",
            "serial_number",
            "type_of_call",
            "root_cause",
            "action_taken",
            "voltage",
            "earthing",
            "part_replaced",
            "indent_required",
            "defective_part_photo",
            "new_part_photo",
            "customer_signature_name",
            "customer_signature",
            "engineer_remarks",
            "site_photos",
            "completion_date",
        ]

        widgets = {

            "work_order": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Work Order Number",
            }),

            "ups_model": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "UPS Model",
            }),

            "serial_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "UPS Serial Number",
            }),

            "type_of_call": forms.Select(attrs={
                "class": "form-select",
            }),

            "root_cause": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Root Cause Analysis",
            }),

            "action_taken": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Action Taken",
            }),

            "voltage": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Measured Voltage (e.g. 230V)",
            }),

            "earthing": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Measured Earthing (e.g. 1.2V)",
            }),

            "part_replaced": forms.CheckboxInput(attrs={
                "class": "form-check-input",
                "role": "switch",
                "id": "partReplacedSwitch",
            }),

            "indent_required": forms.CheckboxInput(attrs={
                "class": "form-check-input",
                "role": "switch",
            }),

            "defective_part_photo": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                "id": "defectivePartPhoto",
            }),

            "new_part_photo": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                "id": "newPartPhoto",
            }),

            "customer_signature_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Customer Signature Name",
            }),

            "customer_signature": forms.HiddenInput(attrs={
                "id": "customerSignatureInput",
            }),

            "engineer_remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Engineer Remarks",
            }),

            "site_photos": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),

            "completion_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),

        }


class EngineerStep1Form(forms.ModelForm):

    complaint_details = forms.CharField(
        label="Complaint Details",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Enter complaint details",
        }),
    )

    class Meta:

        model = EngineerVisitWorkflow

        fields = [
            "complaint_details",
            "step_1_customer_contacted",
            "step_1_problem_confirmed",
            "step_1_problem_confirmation_notes",
            "step_1_location_confirmed",
            "step_1_location_confirmation_notes",
            "step_1_visit_schedule_confirmed",
            "step_1_visit_schedule_at",
        ]

        widgets = {

            "step_1_customer_contacted": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "step_1_problem_confirmed": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "step_1_problem_confirmation_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter confirmed problem details (Optional)",
            }),

            "step_1_location_confirmed": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "step_1_location_confirmation_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter confirmed service location details (Optional)",
            }),

            "step_1_visit_schedule_confirmed": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),

            "step_1_visit_schedule_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),

        }

        labels = {
            "step_1_customer_contacted": "Contact the customer",
            "step_1_problem_confirmed": "Confirm the reported problem",
            "step_1_problem_confirmation_notes": "Confirmed Problem Details",
            "step_1_location_confirmed": "Confirm the service location",
            "step_1_location_confirmation_notes": "Confirmed Service Location Details",
            "step_1_visit_schedule_confirmed": "Confirm the date and time of the site visit",
            "step_1_visit_schedule_at": "Site Visit Date & Time",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["complaint_details"].initial = self.instance.service_request.problem
        self.fields["step_1_visit_schedule_at"].required = True

        if self.instance.step_1_visit_schedule_at:
            self.initial["step_1_visit_schedule_at"] = self.instance.step_1_visit_schedule_at.strftime("%Y-%m-%dT%H:%M")

    def clean(self):

        cleaned_data = super().clean()

        checklist_fields = [
            "step_1_customer_contacted",
            "step_1_problem_confirmed",
            "step_1_location_confirmed",
            "step_1_visit_schedule_confirmed",
        ]

        if not all(cleaned_data.get(field) for field in checklist_fields):
            raise forms.ValidationError("Complete all mandatory checklist items before proceeding.")

        return cleaned_data

    def save(self, commit=True):

        instance = super().save(commit=False)
        instance.service_request.problem = self.cleaned_data["complaint_details"]
        instance.step_1_completed_at = timezone.now()

        if commit:
            instance.service_request.save(update_fields=["problem", "updated_at"])
            instance.save()

        return instance


class EngineerStep2Form(forms.ModelForm):

    step_2_model_label_photos = MultipleFileField(
        required=False,
        widget=MultiFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        }),
        label="Model/Serial Number Label Photo",
    )

    class Meta:

        model = EngineerVisitWorkflow

        fields = [
            "step_2_model_number",
            "step_2_serial_number",
            "step_2_model_label_photos",
            "step_2_complaint_match_status",
        ]

        widgets = {

            "step_2_model_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter equipment model number",
            }),

            "step_2_serial_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter equipment serial number",
            }),

            "step_2_complaint_match_status": forms.Select(attrs={
                "class": "form-select",
            }),

        }

        labels = {
            "step_2_model_number": "Equipment Model Number",
            "step_2_serial_number": "Equipment Serial Number",
            "step_2_complaint_match_status": "Complaint Record Match Status",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["step_2_model_number"].required = True
        self.fields["step_2_serial_number"].required = True
        self.fields["step_2_complaint_match_status"].required = True
        self.fields["step_2_complaint_match_status"].choices = [
            ("", "Select Verification Status"),
            *EngineerVisitWorkflow.COMPLAINT_MATCH_CHOICES,
        ]

    def clean(self):

        cleaned_data = super().clean()
        uploads = self.files.getlist("step_2_model_label_photos")
        has_photos = bool(uploads) or bool(self.instance.get_model_serial_images())

        if not has_photos:
            self.add_error("step_2_model_label_photos", "Model/Serial Number Label Photo is mandatory.")

        return cleaned_data

    def save(self, commit=True):

        instance = super().save(commit=False)
        instance.step_2_completed_at = timezone.now()

        uploads = self.files.getlist("step_2_model_label_photos")

        if commit:
            instance.save()
            if uploads:
                instance.additional_images.filter(image_type="MODEL_SERIAL").delete()
                instance.step_2_model_label_photo = uploads[0]
                instance.save(update_fields=["step_2_model_label_photo", "updated_at"])

                for upload in uploads[1:]:
                    WorkflowAdditionalImage.objects.create(
                        workflow=instance,
                        image_type="MODEL_SERIAL",
                        image=upload,
                    )

        return instance


class EngineerStep3Form(forms.ModelForm):

    class Meta:

        model = EngineerVisitWorkflow

        fields = [
            "step_3_problem_analysis",
            "step_3_system_data",
            "step_3_category_data",
            "step_3_additional_observations",
        ]

        widgets = {

            "step_3_problem_analysis": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter problem analysis",
            }),

            "step_3_system_data": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter system data",
            }),

            "step_3_category_data": forms.HiddenInput(),

            "step_3_additional_observations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional observations",
            }),

        }

        labels = {
            "step_3_problem_analysis": "Problem Analysis",
            "step_3_system_data": "System Data",
            "step_3_additional_observations": "Additional Observations",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["step_3_problem_analysis"].required = True
        self.fields["step_3_system_data"].required = True

    def clean_step_3_category_data(self):

        category_data = self.cleaned_data.get("step_3_category_data") or []

        if isinstance(category_data, str):
            try:
                category_data = json.loads(category_data)
            except json.JSONDecodeError as error:
                raise forms.ValidationError("Category data is invalid.") from error

        cleaned_rows = []

        for row in category_data:
            row_type = str(row.get("type", "")).strip()
            row_description = str(row.get("description", "")).strip()

            if not row_type and not row_description:
                continue

            cleaned_rows.append({
                "type": row_type,
                "description": row_description,
            })

        return cleaned_rows

    def save(self, commit=True):

        instance = super().save(commit=False)
        instance.step_3_completed_at = timezone.now()

        if commit:
            instance.save()

        return instance


class EngineerStep4Form(forms.ModelForm):

    replacement_required = forms.ChoiceField(
        label="Is defective part replacement needed?",
        choices=[
            ("", "Select an option"),
            ("YES", "Yes"),
            ("NO", "No"),
        ],
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )

    class Meta:

        model = EngineerVisitWorkflow

        fields = [
            "replacement_required",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.instance.step_4_completed_at:
            self.initial["replacement_required"] = "YES" if self.instance.step_4_replacement_required else "NO"

    def save(self, commit=True):

        instance = super().save(commit=False)
        instance.step_4_replacement_required = self.cleaned_data["replacement_required"] == "YES"

        if not instance.step_4_replacement_required:
            instance.step_4_part_decision = ""
            instance.step_4_required_part_details = ""
            instance.step_4_indent_details = ""
            instance.step_4_remarks = ""
            instance.step_4_defective_part_photo = None
            instance.step_5_new_part_name = ""
            instance.step_5_new_part_model_number = ""
            instance.step_5_new_part_serial_number = ""
            instance.step_5_defective_part_model_number = ""
            instance.step_5_defective_part_serial_number = ""
            instance.step_5_replacement_date_time = None
            instance.step_5_installed_part_photo = None
            instance.step_5_defective_part_photo = None
            instance.step_5_completed_at = timezone.now()
        else:
            instance.step_5_completed_at = None

        instance.step_4_completed_at = timezone.now()

        if commit:
            instance.save()

        return instance


class EngineerStep5Form(forms.ModelForm):

    step_4_defective_part_photos = MultipleFileField(
        required=False,
        widget=MultiFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        }),
        label="Defective Part Photo",
    )

    step_5_installed_part_photos = MultipleFileField(
        required=False,
        widget=MultiFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        }),
        label="Replaced Part Photo",
    )

    class Meta:

        model = EngineerVisitWorkflow

        fields = [
            "step_4_part_decision",
            "step_4_defective_part_photos",
            "step_5_installed_part_photos",
            "step_5_new_part_model_number",
            "step_5_new_part_serial_number",
        ]

        widgets = {

            "step_4_part_decision": forms.Select(attrs={
                "class": "form-select",
            }),

            "step_5_new_part_model_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter replaced part model number",
            }),

            "step_5_new_part_serial_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter replaced part serial number",
            }),

        }

        labels = {
            "step_4_part_decision": "Part Status",
            "step_5_new_part_model_number": "Replaced Part Model Number",
            "step_5_new_part_serial_number": "Replaced Part Serial Number",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["step_4_part_decision"].required = True
        self.fields["step_4_part_decision"].choices = [
            ("", "Select Part Status"),
            *EngineerVisitWorkflow.PART_DECISION_CHOICES,
        ]

    def clean(self):

        cleaned_data = super().clean()
        defective_uploads = self.files.getlist("step_4_defective_part_photos")
        installed_uploads = self.files.getlist("step_5_installed_part_photos")

        has_defective_images = bool(defective_uploads) or bool(self.instance.get_defective_part_images())
        has_installed_images = bool(installed_uploads) or bool(self.instance.get_replaced_part_images())

        if not has_defective_images:
            self.add_error("step_4_defective_part_photos", "Defective Part Photo is mandatory.")

        if cleaned_data.get("step_4_part_decision") == "AVAILABLE":
            if not has_installed_images:
                self.add_error("step_5_installed_part_photos", "Replaced Part Photo is mandatory.")

            if not cleaned_data.get("step_5_new_part_model_number"):
                self.add_error("step_5_new_part_model_number", "Replaced Part Model Number is mandatory.")

            if not cleaned_data.get("step_5_new_part_serial_number"):
                self.add_error("step_5_new_part_serial_number", "Replaced Part Serial Number is mandatory.")

        return cleaned_data

    def save(self, commit=True):

        instance = super().save(commit=False)
        defective_uploads = self.files.getlist("step_4_defective_part_photos")
        installed_uploads = self.files.getlist("step_5_installed_part_photos")
        instance.step_5_new_part_name = ""
        instance.step_5_defective_part_model_number = ""
        instance.step_5_defective_part_serial_number = ""
        instance.step_5_replacement_date_time = timezone.now() if instance.step_4_part_decision == "AVAILABLE" else None

        if instance.step_4_part_decision == "NOT_AVAILABLE":
            instance.step_5_installed_part_photo = None
            instance.step_5_new_part_model_number = ""
            instance.step_5_new_part_serial_number = ""

        instance.step_5_completed_at = timezone.now()

        if commit:
            instance.save()
            self._replace_image_group(instance, "DEFECTIVE", defective_uploads, "step_4_defective_part_photo")

            if instance.step_4_part_decision == "AVAILABLE":
                self._replace_image_group(instance, "REPLACED", installed_uploads, "step_5_installed_part_photo")
            else:
                instance.additional_images.filter(image_type="REPLACED").delete()
                instance.step_5_installed_part_photo = None
                instance.save(update_fields=["step_5_installed_part_photo", "updated_at"])

        return instance

    def _replace_image_group(self, instance, image_type, uploads, primary_field_name):

        if not uploads:
            return

        instance.additional_images.filter(image_type=image_type).delete()
        setattr(instance, primary_field_name, uploads[0])
        instance.save(update_fields=[primary_field_name, "updated_at"])

        for upload in uploads[1:]:
            WorkflowAdditionalImage.objects.create(
                workflow=instance,
                image_type=image_type,
                image=upload,
            )


class EngineerStep6Form(forms.Form):

    ups_operational_verified = forms.BooleanField(
        required=True,
        label="Verify UPS is operational",
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input",
        }),
    )

    working_condition_demonstrated = forms.BooleanField(
        required=True,
        label="Demonstrate working condition to customer",
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input",
        }),
    )

    out_of_scope_reported = forms.BooleanField(
        required=False,
        label="Out of Scope",
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input",
        }),
    )

    customer_name = forms.CharField(
        label="Customer Name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter customer name",
        }),
    )

    mobile_number = forms.CharField(
        label="Mobile Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter mobile number",
        }),
    )

    email_address = forms.EmailField(
        required=False,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address",
        }),
    )

    final_engineer_remarks = forms.CharField(
        label="Final Engineer Remarks",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Enter final engineer remarks",
        }),
    )

    installation_images = MultipleFileField(
        required=True,
        widget=MultiFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        }),
        label="Installation Image / Site Photos",
    )

    def clean_mobile_number(self):

        mobile_number = self.cleaned_data["mobile_number"].strip()

        import re
        if not re.match(r"^\d{5} \d{5}$", mobile_number):
            raise forms.ValidationError("Mobile number must follow the format XXXXX XXXXX (5 digits, space, 5 digits).")

        return mobile_number
