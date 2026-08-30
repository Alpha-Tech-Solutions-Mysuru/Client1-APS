import io
import tempfile
from datetime import timedelta
from pathlib import Path

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django.utils.datastructures import MultiValueDict

from accounts.models import User
from accounts.models import UserRole

from .forms import EngineerStep5Form
from .models import CallClosure
from .models import EngineerVisitWorkflow
from .models import ServiceRequest
from .models import WorkflowAdditionalImage
from .retention import cleanup_expired_service_requests


def _build_test_image(name):

    buffer = io.BytesIO()
    image = Image.new("RGB", (40, 40), "white")
    image.save(buffer, format="PNG")

    return SimpleUploadedFile(
        name=name,
        content=buffer.getvalue(),
        content_type="image/png",
    )


@override_settings(SERVICE_REPORT_RETENTION_DAYS=7)
class ServiceRetentionTests(TestCase):

    def setUp(self):

        self.temp_media_dir = tempfile.TemporaryDirectory()
        self.override_media = override_settings(MEDIA_ROOT=self.temp_media_dir.name)
        self.override_media.enable()

        self.engineer = User.objects.create_user(
            username="engineer1",
            password="pass1234",
            role=UserRole.ENGINEER,
            mobile_number="9000000001",
        )

    def tearDown(self):

        self.override_media.disable()
        self.temp_media_dir.cleanup()

    def _create_closed_service(self, client_id, closure_recorded_at):

        service = ServiceRequest.objects.create(
            work_order_number=f"WO-{client_id}",
            client_id=client_id,
            customer_name="Customer",
            mobile_number="9000000002",
            email="customer@example.com",
            address="Address",
            type_of_call="AMC",
            ups_model="UPS-X",
            serial_number=f"SN-{client_id}",
            engineer=self.engineer,
        )

        workflow = EngineerVisitWorkflow.objects.create(
            service_request=service,
            step_2_equipment_photo=_build_test_image("equipment.png"),
            step_3_supporting_photo=_build_test_image("supporting.png"),
            step_5_installed_part_photo=_build_test_image("installed.png"),
        )

        closure = CallClosure.objects.create(
            service_request=service,
            work_order=service.work_order_number,
            ups_model=service.ups_model,
            serial_number=service.serial_number,
            type_of_call=service.type_of_call,
            root_cause="Root cause",
            action_taken="Action taken",
            voltage="230V",
            earthing="Good",
            part_replaced=True,
            indent_required=False,
            defective_part_photo=workflow.step_3_supporting_photo,
            new_part_photo=workflow.step_5_installed_part_photo,
            customer_signature_name="Customer",
            engineer_remarks="Remarks",
            site_photos=workflow.step_2_equipment_photo,
            completion_date=closure_recorded_at.date(),
            customer_mobile_number="9000000002",
            customer_email="customer@example.com",
            out_of_scope_observations="None",
            ups_operational_verified=True,
            working_condition_demonstrated=True,
            closure_recorded_at=closure_recorded_at,
        )

        return service, workflow, closure

    def test_cleanup_deletes_expired_closed_request_and_files(self):

        expired_time = timezone.now() - timedelta(days=8)
        service, workflow, closure = self._create_closed_service("APS-OLD", expired_time)
        file_paths = [
            Path(workflow.step_2_equipment_photo.path),
            Path(workflow.step_3_supporting_photo.path),
            Path(workflow.step_5_installed_part_photo.path),
        ]

        for file_path in file_paths:
            self.assertTrue(file_path.exists())

        deleted_count = cleanup_expired_service_requests()

        self.assertEqual(deleted_count, 1)
        self.assertFalse(ServiceRequest.objects.filter(pk=service.pk).exists())
        self.assertFalse(EngineerVisitWorkflow.objects.filter(pk=workflow.pk).exists())
        self.assertFalse(CallClosure.objects.filter(pk=closure.pk).exists())

        for file_path in file_paths:
            self.assertFalse(file_path.exists())

    def test_cleanup_keeps_recent_closed_request(self):

        recent_time = timezone.now() - timedelta(days=2)
        service, workflow, closure = self._create_closed_service("APS-NEW", recent_time)

        deleted_count = cleanup_expired_service_requests()

        self.assertEqual(deleted_count, 0)
        self.assertTrue(ServiceRequest.objects.filter(pk=service.pk).exists())
        self.assertTrue(EngineerVisitWorkflow.objects.filter(pk=workflow.pk).exists())
        self.assertTrue(CallClosure.objects.filter(pk=closure.pk).exists())


@override_settings(SERVICE_REPORT_RETENTION_DAYS=7)
class EngineerWorkflowFormTests(TestCase):

    def setUp(self):

        self.temp_media_dir = tempfile.TemporaryDirectory()
        self.override_media = override_settings(MEDIA_ROOT=self.temp_media_dir.name)
        self.override_media.enable()

        self.engineer = User.objects.create_user(
            username="engineer2",
            password="pass1234",
            role=UserRole.ENGINEER,
            mobile_number="9000000003",
        )
        self.service = ServiceRequest.objects.create(
            work_order_number="WO-STEP5",
            client_id="APS-STEP5",
            customer_name="Customer",
            mobile_number="9000000004",
            type_of_call="AMC",
            ups_model="UPS-X",
            serial_number="SN-STEP5",
            engineer=self.engineer,
        )
        self.workflow = EngineerVisitWorkflow.objects.create(
            service_request=self.service,
            step_4_replacement_required=True,
        )

    def tearDown(self):

        self.override_media.disable()
        self.temp_media_dir.cleanup()

    def test_step_5_form_saves_multiple_images(self):

        form = EngineerStep5Form(
            data={
                "step_4_part_decision": "AVAILABLE",
                "step_5_new_part_model_number": "MODEL-1",
                "step_5_new_part_serial_number": "SERIAL-1",
            },
            files=MultiValueDict({
                "step_4_defective_part_photos": [
                    _build_test_image("defective-1.png"),
                    _build_test_image("defective-2.png"),
                ],
                "step_5_installed_part_photos": [
                    _build_test_image("replaced-1.png"),
                    _build_test_image("replaced-2.png"),
                ],
            }),
            instance=self.workflow,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.workflow.refresh_from_db()

        self.assertTrue(self.workflow.step_4_defective_part_photo.name.endswith("defective-1.png"))
        self.assertTrue(self.workflow.step_5_installed_part_photo.name.endswith("replaced-1.png"))
        self.assertEqual(
            WorkflowAdditionalImage.objects.filter(workflow=self.workflow, image_type="DEFECTIVE").count(),
            1,
        )
        self.assertEqual(
            WorkflowAdditionalImage.objects.filter(workflow=self.workflow, image_type="REPLACED").count(),
            1,
        )

    def test_step_2_form_saves_multiple_images(self):
        from .forms import EngineerStep2Form

        form = EngineerStep2Form(
            data={
                "step_2_model_number": "MODEL-XYZ",
                "step_2_serial_number": "SERIAL-XYZ",
                "step_2_complaint_match_status": "MATCHED",
            },
            files=MultiValueDict({
                "step_2_model_label_photos": [
                    _build_test_image("label-1.png"),
                    _build_test_image("label-2.png"),
                ],
            }),
            instance=self.workflow,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.workflow.refresh_from_db()

        self.assertTrue(self.workflow.step_2_model_label_photo.name.endswith("label-1.png"))
        self.assertEqual(
            WorkflowAdditionalImage.objects.filter(workflow=self.workflow, image_type="MODEL_SERIAL").count(),
            1,
        )
