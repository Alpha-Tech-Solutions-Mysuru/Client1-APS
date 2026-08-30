from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .decorators import superadmin_required
from .forms import LoginForm
from .forms import PasswordResetForm
from .forms import StaffCreationForm
from .forms import StaffUpdateForm
from .models import User
from .models import UserRole


def admin_login(request):

    if request.user.is_authenticated:

        if request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            return redirect("ups:dashboard")

        return redirect("ups:home")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:

                if user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:

                    messages.error(request, "Please use Engineer Login.")

                    return redirect("accounts:login")

                login(request, user)

                messages.success(request, "Login Successful.")

                return redirect("ups:dashboard")

        messages.error(request, "Invalid Username or Password.")

    context = {
        "form": form,
        "page_title": "Admin / Super Admin Login",
        "login_type": "admin",
    }

    return render(
        request,
        "accounts/login.html",
        context,
    )


def engineer_login(request):

    if request.user.is_authenticated:

        if request.user.role == UserRole.ENGINEER:
            return redirect("ups:dashboard")

        return redirect("ups:home")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:

                if user.role != UserRole.ENGINEER:

                    messages.error(request, "Please use Admin Login.")

                    return redirect("accounts:engineer_login")

                login(request, user)

                messages.success(request, "Login Successful.")

                return redirect("ups:dashboard")

        messages.error(request, "Invalid Username or Password.")

    context = {
        "form": form,
        "page_title": "Engineer Login",
        "login_type": "engineer",
    }

    return render(
        request,
        "accounts/login.html",
        context,
    )


@login_required
def logout_user(request):

    logout(request)

    messages.success(request, "Logged out successfully.")

    return redirect("ups:home")


@superadmin_required
def create_staff(request):

    form = StaffCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        user = form.save(commit=False)
        user.visible_password = form.cleaned_data["password1"]
        user.save()

        request.session["created_username"] = user.username
        request.session["created_password"] = form.cleaned_data["password1"]
        request.session["success_title"] = "User Created Successfully"

        messages.success(request, "Staff created successfully.")

        return redirect("accounts:staff_created_success")

    context = {
        "form": form,
    }

    return render(
        request,
        "accounts/create_staff.html",
        context,
    )


@superadmin_required
def staff_created_success(request):

    username = request.session.get("created_username")
    password = request.session.get("created_password")
    title = request.session.get("success_title", "User Created Successfully")

    if not username or not password:
        return redirect("accounts:manage_staff")

    context = {
        "username": username,
        "password": password,
        "title": title,
    }

    request.session.pop("created_username", None)
    request.session.pop("created_password", None)
    request.session.pop("success_title", None)

    return render(
        request,
        "accounts/staff_created_success.html",
        context,
    )


@superadmin_required
def reset_password(request, pk):

    user = get_object_or_404(User, pk=pk)

    form = PasswordResetForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        new_password = form.cleaned_data["password1"]

        user.set_password(new_password)
        user.visible_password = new_password
        user.save()

        request.session["created_username"] = user.username
        request.session["created_password"] = new_password
        request.session["success_title"] = "Password Reset Successfully"

        messages.success(request, f"Password reset for {user.username} successfully.")

        return redirect("accounts:staff_created_success")

    context = {
        "form": form,
        "staff": user,
    }

    return render(
        request,
        "accounts/reset_password.html",
        context,
    )


@superadmin_required
def manage_staff(request):

    users = User.objects.exclude(
        id=request.user.id,
    ).order_by(
        "username",
    )

    staff_rows = [
        {
            "user": user,
            "edit_form": StaffUpdateForm(
                instance=user,
                prefix=f"user-{user.pk}",
            ),
        }
        for user in users
    ]

    context = {
        "staff_rows": staff_rows,
    }

    return render(
        request,
        "accounts/manage_staff.html",
        context,
    )


@superadmin_required
def update_staff(request, pk):

    user = get_object_or_404(User, pk=pk)

    form = StaffUpdateForm(
        request.POST or None,
        instance=user,
        prefix=f"user-{user.pk}",
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(request, f"{user.username} updated successfully.")

    elif request.method == "POST":

        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")

    return redirect("accounts:manage_staff")


@superadmin_required
def delete_staff(request, pk):

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":

        username = user.username
        user.delete()

        messages.success(request, f"{username} deleted successfully.")

    return redirect("accounts:manage_staff")


@superadmin_required
def organization_profile(request):

    context = {
        "users": User.objects.order_by("username"),
    }

    return render(
        request,
        "accounts/organization_profile.html",
        context,
    )


@superadmin_required
def staff_details(request, pk):

    user = get_object_or_404(User, pk=pk)

    context = {
        "staff": user,
    }

    return render(
        request,
        "accounts/staff_details.html",
        context,
    )


@superadmin_required
def view_staff_password(request, pk):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method.",
            },
            status=405,
        )

    user = get_object_or_404(User, pk=pk)

    superadmin_password = request.POST.get("superadmin_password", "")

    if not request.user.check_password(superadmin_password):

        return JsonResponse(
            {
                "success": False,
                "message": "Super admin password is incorrect.",
            },
            status=400,
        )

    if not user.visible_password:

        return JsonResponse(
            {
                "success": False,
                "message": "Password is not available for this staff account. Reset the staff password once to store a new visible password.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "username": user.username,
            "password": user.visible_password,
        }
    )
