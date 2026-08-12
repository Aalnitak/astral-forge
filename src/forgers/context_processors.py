from forgers.models import ForgerProfile


def request_forger(request):
    if not request.user.is_authenticated:
        return {"request_forger": None}

    try:
        return {"request_forger": request.user.forger_profile}
    except ForgerProfile.DoesNotExist:
        return {"request_forger": None}
