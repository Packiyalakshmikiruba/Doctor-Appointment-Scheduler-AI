from django.shortcuts import redirect
from functools import wraps


def role_required(allowed_roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            return redirect("login")

        return wrapper

    return decorator