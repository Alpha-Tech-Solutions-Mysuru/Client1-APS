from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [

    path("login/", views.admin_login, name="login"),

    path("superadmin-login/", views.admin_login, name="superadmin_login"),

    path("engineer-login/", views.engineer_login, name="engineer_login"),

    path("logout/", views.logout_user, name="logout"),

    path("create-staff/", views.create_staff, name="create_staff"),

    path("manage-staff/", views.manage_staff, name="manage_staff"),

    path("manage-staff/<int:pk>/update/", views.update_staff, name="update_staff"),

    path("manage-staff/<int:pk>/delete/", views.delete_staff, name="delete_staff"),

    path("staff-details/<int:pk>/", views.staff_details, name="staff_details"),

    path("staff-details/<int:pk>/view-password/", views.view_staff_password, name="view_staff_password"),

    path("organization-profile/", views.organization_profile, name="organization_profile"),

    path("staff-created-success/", views.staff_created_success, name="staff_created_success"),

    path("reset-password/<int:pk>/", views.reset_password, name="reset_password"),

]
