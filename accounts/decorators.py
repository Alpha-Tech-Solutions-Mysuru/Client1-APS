from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserRole


def has_role(role):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.role == role:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You are not authorized to access this page.")

            return redirect("ups:home")

        return wrapper

    return decorator


def has_any_role(roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You are not authorized to access this page.")

            return redirect("ups:home")

        return wrapper

    return decorator


def superadmin_required(view_func):

    return has_role(UserRole.SUPERADMIN)(view_func)


def admin_required(view_func):

    return has_any_role(
        [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
        ]
    )(view_func)


def engineer_required(view_func):

    return has_role(UserRole.ENGINEER)(view_func)
