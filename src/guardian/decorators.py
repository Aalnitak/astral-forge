from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from forgers.models import ForgerProfile


def guardian_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            request.forger_profile = request.user.forger_profile
        except ForgerProfile.DoesNotExist:
            messages.error(
                request,
                "Tu usuario necesita un perfil de forjador para entrar al panel guardian.",
            )
            return redirect("home")

        if not request.forger_profile.is_guardian:
            messages.error(
                request,
                "Tu perfil no tiene permisos de guardian.",
            )
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper
