import base64
import io
import json
from datetime import timedelta
from urllib.parse import quote

from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.html import escape
from django.utils import timezone
from PIL import Image
from PIL import ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle

from accounts.decorators import admin_required
from accounts.decorators import engineer_required
from accounts.models import UserRole

from .forms import EngineerStep1Form
from .forms import EngineerStep2Form
from .forms import EngineerStep3Form
from .forms import EngineerStep4Form
from .forms import EngineerStep5Form
from .forms import EngineerStep6Form
from .forms import ServiceRequestForm
from .models import CallClosure
from .models import EngineerVisitWorkflow
from .models import ServiceRequest
from .retention import get_service_retention_days


ENGINEER_STEP_TITLES = {
    1: "Engineer SOP",
    2: "Site Visit Verification",
    3: "Site Inspection & Problem Analysis",
    4: "Part Replacement Decision",
    5: "Part Replacement",
    6: "Call Closure",
}

ENGINEER_STEP_FLOW = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
}


def home(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return redirect("ups:dashboard")

    if request.user.role == UserRole.ENGINEER:
        return redirect("ups:dashboard")

    return redirect("accounts:login")


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:

        context = {
            "total_requests": ServiceRequest.objects.count(),
            "open_requests": ServiceRequest.objects.filter(closure__isnull=True).count(),
            "closed_requests": ServiceRequest.objects.filter(
                closure__approval_status="APPROVED",
            ).count(),
        }

    else:

        context = {
            "total_calls": ServiceRequest.objects.filter(engineer=request.user).count(),
            "open_calls": ServiceRequest.objects.filter(engineer=request.user, closure__isnull=True).count(),
            "closed_calls": ServiceRequest.objects.filter(
                engineer=request.user,
                closure__approval_status="APPROVED",
            ).count(),
        }

    return render(
        request,
        "ups/dashboard.html",
        context,
    )


@admin_required
def create_form(request):

    if request.method == "POST":

        form = ServiceRequestForm(request.POST)

        if form.is_valid():

            service = form.save()

            whatsapp_url = _build_whatsapp_url(service)

            return JsonResponse({
                "success": True,
                "whatsapp": whatsapp_url,
            })

        return JsonResponse({
            "success": False,
            "errors": form.errors,
        })

    form = ServiceRequestForm()

    return render(
        request,
        "ups/create_form.html",
        {
            "form": form,
        },
    )


@admin_required
def view_form(request):

    requests = ServiceRequest.objects.order_by(
        "-created_at",
    )

    context = {
        "requests": [
            {
                "service": service,
                "remaining_days": _get_remaining_storage_days(service),
            }
            for service in requests
        ],
        "edit_form": ServiceRequestForm(),
    }

    return render(
        request,
        "ups/view_form.html",
        context,
    )


@admin_required
def edit_form(request, pk):

    service = get_object_or_404(
        ServiceRequest,
        pk=pk,
    )

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request method.",
        }, status=405)

    form = ServiceRequestForm(
        request.POST,
        instance=service,
    )

    if not form.is_valid():
        return JsonResponse({
            "success": False,
            "errors": form.errors,
        }, status=400)

    updated_service = form.save()

    return JsonResponse({
        "success": True,
        "whatsapp": _build_whatsapp_url(updated_service, heading="APS SERVICE REQUEST UPDATED"),
    })


def request_details(request, pk):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    service = get_object_or_404(
        ServiceRequest,
        pk=pk,
    )

    if request.user.role == UserRole.ENGINEER and service.engineer != request.user:

        messages.error(request, "You are not authorized to view this request.")

        return redirect("ups:dashboard")

    context = {
        "service": service,
        "remaining_days": _get_remaining_storage_days(service),
        "existing_defective_images": service.workflow.get_defective_part_images() if hasattr(service, "workflow") else [],
        "existing_replaced_images": service.workflow.get_replaced_part_images() if hasattr(service, "workflow") else [],
        "can_approve_closure": (
            request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]
            and hasattr(service, "closure")
            and service.closure.approval_status == "PENDING"
        ),
    }

    return render(
        request,
        "ups/request_details.html",
        context,
    )


def _get_remaining_storage_days(service):

    if not hasattr(service, "closure"):
        return None

    base_date = service.closure.closure_recorded_at.date() if service.closure.closure_recorded_at else service.closure.completion_date
    expiry_date = base_date + timedelta(days=get_service_retention_days())

    return max((expiry_date - timezone.localdate()).days, 0)


def _build_whatsapp_message(service, heading="APS SERVICE REQUEST"):

    return f"""
{heading}

Client ID : {service.client_id}

Work Order : {service.work_order_number}

Customer : {service.customer_name}

Mobile : {service.mobile_number}

Email : {service.email or "-"}

Address : {service.address or "-"}

Type Of Call : {service.get_type_of_call_display()}

UPS Model : {service.ups_model}

Serial No : {service.serial_number}

Regards,
APS
""".strip()


def _build_whatsapp_url(service, heading="APS SERVICE REQUEST"):

    message = _build_whatsapp_message(service, heading=heading)
    return f"https://wa.me/91{service.engineer.mobile_number}?text={quote(message)}"


def _collect_pdf_images(service):

    images = []
    seen_names = set()

    if hasattr(service, "workflow"):
        workflow = service.workflow
        
        if workflow.step_2_equipment_photo and getattr(workflow.step_2_equipment_photo, "name", ""):
            images.append(("Step 2 - Equipment Photo", workflow.step_2_equipment_photo))
            seen_names.add(workflow.step_2_equipment_photo.name)

        for index, image_field in enumerate(workflow.get_model_serial_images(), start=1):
            if getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append((f"Step 2 - Model/Serial Label Photo {index}", image_field))
                seen_names.add(image_field.name)

        # Legacy fallback for older serial labels
        if workflow.step_2_serial_label_photo and getattr(workflow.step_2_serial_label_photo, "name", "") and workflow.step_2_serial_label_photo.name not in seen_names:
            images.append(("Step 2 - Serial Label Photo", workflow.step_2_serial_label_photo))
            seen_names.add(workflow.step_2_serial_label_photo.name)

        if workflow.step_3_supporting_photo and getattr(workflow.step_3_supporting_photo, "name", "") and workflow.step_3_supporting_photo.name not in seen_names:
            images.append(("Step 3 - Supporting Photo", workflow.step_3_supporting_photo))
            seen_names.add(workflow.step_3_supporting_photo.name)

        for index, image_field in enumerate(workflow.get_defective_part_images(), start=1):
            if getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append((f"Step 5 - Defective Part Photo {index}", image_field))
                seen_names.add(image_field.name)

        for index, image_field in enumerate(workflow.get_replaced_part_images(), start=1):
            if getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append((f"Step 5 - Replaced Part Photo {index}", image_field))
                seen_names.add(image_field.name)

    if hasattr(service, "closure"):
        closure = service.closure
        closure_fields = [
            ("Step 6 - Closure Defective Part Photo", closure.defective_part_photo),
            ("Step 6 - Closure New Part Photo", closure.new_part_photo),
        ]

        for label, image_field in closure_fields:
            if image_field and getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append((label, image_field))
                seen_names.add(image_field.name)

        for index, image_field in enumerate(closure.get_installation_images(), start=1):
            if getattr(image_field, "name", "") and image_field.name not in seen_names:
                images.append((f"Step 6 - Installation Image {index}", image_field))
                seen_names.add(image_field.name)

    return images


def _prepare_pdf_image(image_field, max_width=6.5 * inch, max_height=4.5 * inch):

    if not image_field or not getattr(image_field, "name", ""):
        return None

    try:
        image_field.open("rb")
        opened_image = Image.open(image_field)
        opened_image = ImageOps.exif_transpose(opened_image).convert("RGB")
        opened_image.thumbnail((int(max_width), int(max_height)))
        buffer = io.BytesIO()
        opened_image.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
        pdf_image = PdfImage(buffer)
        pdf_image._buffer = buffer
        pdf_image.drawWidth = opened_image.width
        pdf_image.drawHeight = opened_image.height
        image_field.close()
        return pdf_image
    except Exception:
        return None


def _build_request_pdf(service):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ServiceReportTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=12,
        textColor=colors.black,
    )
    section_style = ParagraphStyle(
        "ServiceReportSection",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.black,
    )
    body_style = ParagraphStyle(
        "ServiceReportBody",
        parent=styles["BodyText"],
        fontSize=14,
        leading=18,
        textColor=colors.black,
    )
    story = [
        Paragraph("Alternate Power Supplies Service Report", title_style),
        Spacer(1, 6),
    ]

    create_form_rows = [
        ("Case ID", service.client_id),
        ("Work Order Number", service.work_order_number or "-"),
        ("Customer Name", service.customer_name),
        ("Company Name", service.company_name or "-"),
        ("Mobile Number", service.mobile_number),
        ("Email", service.email or "-"),
        ("Address", service.address or "-"),
        ("City", service.city or "-"),
        ("State", service.state or "-"),
        ("Pincode", service.pincode or "-"),
        ("Type Of Call", service.get_type_of_call_display() or "-"),
        ("UPS Make", service.ups_make or "-"),
        ("UPS Model", service.ups_model),
        ("Serial Number", service.serial_number),
        ("KVA", service.kva or "-"),
        ("Battery Details", service.battery_details or "-"),
        ("Problem / Complaint", service.problem or "-"),
        ("Assigned Engineer", f"{service.engineer.first_name} {service.engineer.last_name}".strip() or service.engineer.username),
        ("Created At", timezone.localtime(service.created_at).strftime("%d-%m-%Y %H:%M")),
    ]

    workflow = getattr(service, "workflow", None)
    closure = getattr(service, "closure", None)
    category_rows = _get_workflow_categories(workflow)
    category_summary = _get_category_summary_text(category_rows)

    section_rows = [
        ("Create Form Data", create_form_rows),
    ]

    if workflow:
        section_rows.extend([
            ("Step 1 - Engineer SOP", [
                ("Customer Contacted", "Yes" if workflow.step_1_customer_contacted else "No"),
                ("Problem Confirmed", "Yes" if workflow.step_1_problem_confirmed else "No"),
                ("Location Confirmed", "Yes" if workflow.step_1_location_confirmed else "No"),
                ("Visit Date/Time Confirmed", "Yes" if workflow.step_1_visit_schedule_confirmed else "No"),
                ("Remarks", workflow.step_1_remarks or "-"),
                ("Completed At", timezone.localtime(workflow.step_1_completed_at).strftime("%d-%m-%Y %H:%M") if workflow.step_1_completed_at else "-"),
            ]),
            ("Step 2 - Site Visit Verification", [
                ("Equipment Model Number", workflow.step_2_model_number or "-"),
                ("Equipment Serial Number", workflow.step_2_serial_number or "-"),
                ("Complaint Match Status", workflow.get_step_2_complaint_match_status_display() or "-"),
                ("Completed At", timezone.localtime(workflow.step_2_completed_at).strftime("%d-%m-%Y %H:%M") if workflow.step_2_completed_at else "-"),
            ]),
            ("Step 3 - Site Inspection & Problem Analysis", [
                ("Problem Analysis", workflow.step_3_problem_analysis or "-"),
                ("System Data", workflow.step_3_system_data or "-"),
                ("Categories", category_summary or "-"),
                ("Additional Observations", workflow.step_3_additional_observations or "-"),
                ("Completed At", timezone.localtime(workflow.step_3_completed_at).strftime("%d-%m-%Y %H:%M") if workflow.step_3_completed_at else "-"),
            ]),
            ("Step 4 - Part Replacement Decision", [
                ("Replacement Decision", workflow.get_step_4_part_decision_display() or "-"),
                ("Required Part Details", workflow.step_4_required_part_details or "-"),
                ("Indent Details", workflow.step_4_indent_details or "-"),
                ("Remarks", workflow.step_4_remarks or "-"),
                ("Completed At", timezone.localtime(workflow.step_4_completed_at).strftime("%d-%m-%Y %H:%M") if workflow.step_4_completed_at else "-"),
            ]),
            ("Step 5 - Part Replacement", [
                ("New Part Name", workflow.step_5_new_part_name or "-"),
                ("New Part Model Number", workflow.step_5_new_part_model_number or "-"),
                ("New Part Serial Number", workflow.step_5_new_part_serial_number or "-"),
                ("Defective Part Model Number", workflow.step_5_defective_part_model_number or "-"),
                ("Defective Part Serial Number", workflow.step_5_defective_part_serial_number or "-"),
                ("Replacement Date & Time", timezone.localtime(workflow.step_5_replacement_date_time).strftime("%d-%m-%Y %H:%M") if workflow.step_5_replacement_date_time else "-"),
                ("Completed At", timezone.localtime(workflow.step_5_completed_at).strftime("%d-%m-%Y %H:%M") if workflow.step_5_completed_at else "-"),
            ]),
        ])

    if closure:
        section_rows.append(
            ("Step 6 - Call Closure", [
                ("Completion Date", closure.completion_date.strftime("%d-%m-%Y") if closure.completion_date else "-"),
                ("Closure Recorded At", timezone.localtime(closure.closure_recorded_at).strftime("%d-%m-%Y %H:%M") if closure.closure_recorded_at else "-"),
                ("UPS Operational Verified", "Yes" if closure.ups_operational_verified else "No"),
                ("Working Condition Demonstrated", "Yes" if closure.working_condition_demonstrated else "No"),
                ("Customer Name", closure.customer_signature_name or "-"),
                ("Customer Mobile", closure.customer_mobile_number or "-"),
                ("Customer Email", closure.customer_email or "-"),
                ("Root Cause", closure.root_cause or "-"),
                ("Action Taken", closure.action_taken or "-"),
                ("Voltage", closure.voltage or "-"),
                ("Earthing", closure.earthing or "-"),
                ("Part Replaced", "Yes" if closure.part_replaced else "No"),
                ("Indent Required", "Yes" if closure.indent_required else "No"),
                ("Engineer Remarks", closure.engineer_remarks or "-"),
                ("Out-of-Scope Observations", closure.out_of_scope_observations or "-"),
            ])
        )

    for section_title, rows in section_rows:
        story.append(Paragraph(section_title, section_style))
        table_data = []
        for label, value in rows:
            safe_label = escape(str(label or "-"))
            safe_value = escape(str(value or "-")).replace("\n", "<br/>")
            table_data.append([
                Paragraph(f"<b>{safe_label}</b>", body_style),
                Paragraph(safe_value, body_style),
            ])
        section_table = Table(table_data, colWidths=[170, 330], hAlign="LEFT")
        section_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee3")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(section_table)
        story.append(Spacer(1, 8))

    image_entries = _collect_pdf_images(service)

    if image_entries:
        story.append(Paragraph("Engineer Uploaded Images", section_style))

        for label, image_field in image_entries:
            story.append(Paragraph(str(label), body_style))
            pdf_image = _prepare_pdf_image(image_field)
            if pdf_image:
                story.append(Spacer(1, 4))
                story.append(pdf_image)
            else:
                story.append(Paragraph("Image could not be loaded.", body_style))
            story.append(Spacer(1, 10))

    if closure and closure.customer_signature:
        story.append(Paragraph("Customer Signature", section_style))

        try:
            signature_data = closure.customer_signature.split(",", 1)[1]
            signature_image = Image.open(io.BytesIO(base64.b64decode(signature_data)))
            signature_image = ImageOps.exif_transpose(signature_image).convert("RGB")
            signature_image.thumbnail((400, 140))
            signature_buffer = io.BytesIO()
            signature_image.save(signature_buffer, format="JPEG", quality=90)
            signature_buffer.seek(0)
            pdf_signature = PdfImage(signature_buffer)
            pdf_signature._buffer = signature_buffer
            pdf_signature.drawWidth = signature_image.width
            pdf_signature.drawHeight = signature_image.height
            story.append(pdf_signature)
        except Exception:
            story.append(Paragraph("Signature could not be loaded.", body_style))

    doc.build(story)
    buffer.seek(0)

    return buffer


@admin_required
def export_request_pdf(request, pk):

    service = get_object_or_404(
        ServiceRequest,
        pk=pk,
    )

    if not hasattr(service, "closure") or service.closure.approval_status != "APPROVED":

        messages.error(request, "Download is available only after admin approval.")

        return redirect("ups:request_details", pk=service.pk)

    pdf_buffer = _build_request_pdf(service)

    response = HttpResponse(
        pdf_buffer.getvalue(),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{service.client_id}-service-report.pdf"'

    return response


def _get_engineer_service(request, pk):

    return get_object_or_404(
        ServiceRequest,
        pk=pk,
        engineer=request.user,
    )


def _get_workflow(service):

    workflow, _ = EngineerVisitWorkflow.objects.get_or_create(
        service_request=service,
    )

    return workflow


def _is_step_completed(service, workflow, step_number):

    if step_number == 1:
        return bool(workflow.step_1_completed_at)

    if step_number == 2:
        return bool(workflow.step_2_completed_at)

    if step_number == 3:
        return bool(workflow.step_3_completed_at)

    if step_number == 4:
        return bool(workflow.step_4_completed_at)

    if step_number == 5:
        return bool(workflow.step_5_completed_at)

    if step_number == 6:
        return hasattr(service, "closure")

    return False


def _get_step_url_name(step_number):

    return {
        1: "ups:close_call",
        2: "ups:engineer_step_2",
        3: "ups:engineer_step_3",
        4: "ups:engineer_step_4",
        5: "ups:engineer_step_5",
        6: "ups:engineer_step_6",
    }[step_number]


def _get_display_step_number(step_number):

    return ENGINEER_STEP_FLOW[step_number]


def _ensure_step_access(request, service, workflow, step_number):

    if hasattr(service, "closure"):

        if service.closure.approval_status == "APPROVED":
            messages.warning(request, f"Call {service.client_id} is already completed.")
        else:
            messages.warning(request, f"Call {service.client_id} is already submitted for admin approval.")

        return redirect("ups:request_details", pk=service.pk)

    for previous_step in range(1, step_number):

        if not _is_step_completed(service, workflow, previous_step):

            messages.error(
                request,
                f"Complete Step {_get_display_step_number(previous_step)} before proceeding to Step {_get_display_step_number(step_number)}.",
            )

            return redirect(
                _get_step_url_name(previous_step),
                pk=service.pk,
            )

    return None


def _get_service_summary(service):

    return [
        ("Case ID", service.client_id),
        ("Work Order", service.work_order_number or "-"),
        ("Customer", service.customer_name),
        ("UPS Model", service.ups_model),
        ("Serial Number", service.serial_number),
    ]


def _get_step_progress(service, workflow, current_step):

    progress = []

    for actual_step, display_step in ENGINEER_STEP_FLOW.items():

        progress.append({
            "number": display_step,
            "title": ENGINEER_STEP_TITLES[display_step],
            "url": _get_step_url_name(actual_step),
            "completed": _is_step_completed(service, workflow, actual_step),
            "active": actual_step == current_step,
        })

    return progress


def _get_existing_files(workflow):

    existing_files = []

    file_fields = [
        "step_2_model_label_photo",
        "step_2_serial_label_photo",
        "step_4_defective_part_photo",
        "step_5_installed_part_photo",
        "step_5_defective_part_photo",
    ]

    for field_name in file_fields:

        field_file = getattr(workflow, field_name)

        if field_file:
            existing_files.append({
                "name": field_name,
                "url": field_file.url,
            })

    return existing_files


def _get_workflow_categories(workflow):

    if not workflow:
        return []

    category_rows = workflow.step_3_category_data or []

    if not isinstance(category_rows, list):
        return []

    return [
        {
            "type": str(row.get("type", "")).strip(),
            "description": str(row.get("description", "")).strip(),
        }
        for row in category_rows
        if str(row.get("type", "")).strip() or str(row.get("description", "")).strip()
    ]


def _get_category_summary_text(category_rows):

    return "\n".join(
        f"{row['type'] or '-'}: {row['description'] or '-'}"
        for row in category_rows
    )


def _get_form_category_rows(form, workflow):

    if form.is_bound:
        raw_value = form["step_3_category_data"].value() if "step_3_category_data" in form.fields else None

        if raw_value:
            try:
                parsed_rows = json.loads(raw_value)
            except (TypeError, json.JSONDecodeError):
                parsed_rows = []
        else:
            parsed_rows = []

        if isinstance(parsed_rows, list):
            return [
                {
                    "type": str(row.get("type", "")).strip(),
                    "description": str(row.get("description", "")).strip(),
                }
                for row in parsed_rows
                if str(row.get("type", "")).strip() or str(row.get("description", "")).strip()
            ]

    return _get_workflow_categories(workflow)


def _render_engineer_step(request, service, workflow, form, step_number, submit_label):

    category_rows = _get_form_category_rows(form, workflow)

    return render(
        request,
        "ups/engineer_step_form.html",
        {
            "service": service,
            "workflow": workflow,
            "form": form,
            "step_number": ENGINEER_STEP_FLOW[step_number],
            "step_title": ENGINEER_STEP_TITLES[step_number],
            "step_progress": _get_step_progress(service, workflow, step_number),
            "service_summary": _get_service_summary(service),
            "existing_files": _get_existing_files(workflow),
            "existing_model_serial_images": workflow.get_model_serial_images(),
            "existing_defective_images": workflow.get_defective_part_images(),
            "existing_replaced_images": workflow.get_replaced_part_images(),
            "existing_installation_images": service.closure.get_installation_images() if hasattr(service, "closure") else [],
            "category_rows": category_rows,
            "category_rows_json": json.dumps(category_rows),
            "submit_label": submit_label,
        },
    )


@engineer_required
def my_calls(request):

    calls = ServiceRequest.objects.filter(
        engineer=request.user,
    ).order_by(
        "-created_at",
    )

    return render(
        request,
        "ups/my_calls.html",
        {
            "calls": calls,
        },
    )


@engineer_required
def close_call_list(request):

    calls = ServiceRequest.objects.filter(
        engineer=request.user,
        closure__isnull=True,
    ).order_by(
        "-created_at",
    )

    return render(
        request,
        "ups/close_call_list.html",
        {
            "calls": calls,
        },
    )


@engineer_required
def close_call(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    if hasattr(service, "closure"):

        if service.closure.approval_status == "APPROVED":
            messages.warning(request, f"Call {service.client_id} is already completed.")
        else:
            messages.warning(request, f"Call {service.client_id} is already submitted for admin approval.")

        return redirect("ups:request_details", pk=service.pk)

    form = EngineerStep1Form(
        request.POST or None,
        instance=workflow,
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(request, "Step 1 saved successfully.")

        return redirect("ups:engineer_step_2", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        1,
        "Save & Next",
    )


@engineer_required
def engineer_step_2(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    blocked_response = _ensure_step_access(request, service, workflow, 2)

    if blocked_response:
        return blocked_response

    form = EngineerStep2Form(
        request.POST or None,
        request.FILES or None,
        instance=workflow,
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(request, "Step 2 saved successfully.")

        return redirect("ups:engineer_step_3", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        2,
        "Save & Next",
    )


@engineer_required
def engineer_step_3(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    blocked_response = _ensure_step_access(request, service, workflow, 3)

    if blocked_response:
        return blocked_response

    form = EngineerStep3Form(
        request.POST or None,
        request.FILES or None,
        instance=workflow,
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(request, "Step 3 saved successfully.")

        return redirect("ups:engineer_step_4", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        3,
        "Save & Next",
    )


@engineer_required
def engineer_step_4(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    blocked_response = _ensure_step_access(request, service, workflow, 4)

    if blocked_response:
        return blocked_response

    form = EngineerStep4Form(
        request.POST or None,
        request.FILES or None,
        instance=workflow,
    )

    if request.method == "POST" and form.is_valid():

        workflow = form.save()

        messages.success(request, "Step 4 saved successfully.")

        if not workflow.step_4_replacement_required:
            return redirect("ups:engineer_step_6", pk=service.pk)

        return redirect("ups:engineer_step_5", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        4,
        "Save & Next",
    )


@engineer_required
def engineer_step_5(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    blocked_response = _ensure_step_access(request, service, workflow, 5)

    if blocked_response:
        return blocked_response

    if not workflow.step_4_replacement_required:
        return redirect("ups:engineer_step_6", pk=service.pk)

    form = EngineerStep5Form(
        request.POST or None,
        request.FILES or None,
        instance=workflow,
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(request, "Step 5 saved successfully.")

        return redirect("ups:engineer_step_6", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        5,
        "Save & Next",
    )


@engineer_required
def engineer_step_6(request, pk):

    service = _get_engineer_service(request, pk)
    workflow = _get_workflow(service)

    blocked_response = _ensure_step_access(request, service, workflow, 6)

    if blocked_response:
        return blocked_response

    form = EngineerStep6Form(
        request.POST or None,
        request.FILES or None,
        initial={
            "customer_name": service.customer_name,
            "mobile_number": service.mobile_number,
            "email_address": service.email,
        },
    )

    if request.method == "POST" and form.is_valid():

        data = form.cleaned_data
        installation_uploads = request.FILES.getlist("installation_images")

        part_replaced = workflow.step_4_replacement_required and workflow.step_4_part_decision == "AVAILABLE"
        indent_required = workflow.step_4_replacement_required and workflow.step_4_part_decision == "NOT_AVAILABLE"

        if not workflow.step_4_replacement_required:
            action_taken = "No defective part replacement required."
        elif indent_required:
            action_taken = "Indent request raised for defective part replacement."
        else:
            action_taken = "Defective part replaced."

        closure = CallClosure(
            service_request=service,
            work_order=service.work_order_number,
            ups_model=service.ups_model,
            serial_number=service.serial_number,
            type_of_call=service.type_of_call,
            root_cause=workflow.step_3_problem_analysis,
            action_taken=action_taken,
            voltage=workflow.step_3_system_data[:50],
            earthing=_get_category_summary_text(_get_workflow_categories(workflow))[:50],
            part_replaced=part_replaced,
            indent_required=indent_required,
            defective_part_photo=workflow.step_4_defective_part_photo,
            new_part_photo=workflow.step_5_installed_part_photo,
            customer_signature_name=data["customer_name"],
            customer_signature="",
            engineer_remarks=data["final_engineer_remarks"],
            site_photos=installation_uploads[0] if installation_uploads else None,
            completion_date=timezone.localdate(),
            customer_mobile_number=data["mobile_number"],
            customer_email=data["email_address"],
            out_of_scope_observations="Yes" if data["out_of_scope_reported"] else "",
            out_of_scope_reported=data["out_of_scope_reported"],
            ups_operational_verified=data["ups_operational_verified"],
            working_condition_demonstrated=data["working_condition_demonstrated"],
            closure_recorded_at=timezone.now(),
            approval_status="PENDING",
        )

        closure.save()

        if len(installation_uploads) > 1:
            for upload in installation_uploads[1:]:
                ClosureAdditionalImage.objects.create(
                    closure=closure,
                    image=upload,
                )

        messages.success(request, f"Call {service.client_id} submitted for admin approval.")

        return redirect("ups:request_details", pk=service.pk)

    return _render_engineer_step(
        request,
        service,
        workflow,
        form,
        6,
        "Submit And Wait For Admin Approval",
    )


@admin_required
def approve_call_closure(request, pk):

    service = get_object_or_404(
        ServiceRequest,
        pk=pk,
    )

    closure = getattr(service, "closure", None)

    if request.method != "POST" or not closure or closure.approval_status == "APPROVED":
        return redirect("ups:request_details", pk=service.pk)

    closure.approval_status = "APPROVED"
    closure.approved_at = timezone.now()
    closure.save(update_fields=["approval_status", "approved_at", "updated_at"])

    messages.success(request, f"Call {service.client_id} marked as complete.")

    return redirect("ups:request_details", pk=service.pk)
