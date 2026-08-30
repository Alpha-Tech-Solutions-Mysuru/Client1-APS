from datetime import timedelta
from threading import Lock

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils import timezone

from .models import ServiceRequest


_cleanup_lock = Lock()


def get_service_retention_days():

    return getattr(settings, "SERVICE_REPORT_RETENTION_DAYS", 7)


def _get_retention_cutoff():

    return timezone.now() - timedelta(days=get_service_retention_days())


def _collect_service_file_names(service):

    file_names = set()
    file_field_names = []

    workflow = getattr(service, "workflow", None)

    if workflow:
        file_field_names.extend([
            workflow.step_2_equipment_photo,
            workflow.step_2_model_label_photo,
            workflow.step_2_serial_label_photo,
            workflow.step_3_supporting_photo,
            workflow.step_4_defective_part_photo,
            workflow.step_5_installed_part_photo,
            workflow.step_5_defective_part_photo,
        ])

        for additional_image in workflow.additional_images.all():
            file_field_names.append(additional_image.image)

    closure = getattr(service, "closure", None)

    if closure:
        file_field_names.extend([
            closure.defective_part_photo,
            closure.new_part_photo,
            closure.site_photos,
        ])

    for field_file in file_field_names:
        if field_file and getattr(field_file, "name", ""):
            file_names.add(field_file.name)

    return file_names


def cleanup_expired_service_requests():

    with _cleanup_lock:
        expired_services = list(
            ServiceRequest.objects.select_related(
                "workflow",
                "closure",
            ).prefetch_related(
                "workflow__additional_images",
            ).filter(
                Q(closure__closure_recorded_at__lt=_get_retention_cutoff()) |
                Q(
                    closure__closure_recorded_at__isnull=True,
                    closure__completion_date__lt=timezone.localdate() - timedelta(days=get_service_retention_days()),
                )
            )
        )

        deleted_count = 0

        for service in expired_services:
            for file_name in _collect_service_file_names(service):
                if default_storage.exists(file_name):
                    default_storage.delete(file_name)

            service.delete()
            deleted_count += 1

        return deleted_count
