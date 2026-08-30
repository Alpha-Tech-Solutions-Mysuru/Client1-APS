from django.urls import path

from . import views

app_name = "ups"

urlpatterns = [

    path("", views.home, name="home"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("create-form/", views.create_form, name="create_form"),

    path("view-form/", views.view_form, name="view_form"),

    path(
        "request/<int:pk>/edit/",
        views.edit_form,
        name="edit_form",
    ),

    path(
        "request/<int:pk>/",
        views.request_details,
        name="request_details",
    ),

    path(
        "request/<int:pk>/download-pdf/",
        views.export_request_pdf,
        name="export_request_pdf",
    ),

    path(
        "request/<int:pk>/approve-closure/",
        views.approve_call_closure,
        name="approve_call_closure",
    ),

    path("my-calls/", views.my_calls, name="my_calls"),

    path("close-calls/", views.close_call_list, name="close_call_list"),

    path("close-call/<int:pk>/", views.close_call, name="close_call"),

    path("close-call/<int:pk>/step-2/", views.engineer_step_2, name="engineer_step_2"),

    path("close-call/<int:pk>/step-3/", views.engineer_step_3, name="engineer_step_3"),

    path("close-call/<int:pk>/step-4/", views.engineer_step_4, name="engineer_step_4"),

    path("close-call/<int:pk>/step-5/", views.engineer_step_5, name="engineer_step_5"),

    path("close-call/<int:pk>/step-6/", views.engineer_step_6, name="engineer_step_6"),

]
