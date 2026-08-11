from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


def health(_):
    return JsonResponse({"status": "ok"})


@ensure_csrf_cookie
def home(request):
    uri_path = request.path
    return render(
        request,
        "home.html",
        {
            "database": settings.DATABASE_URL.split("/")[-1] or "Default (SQLite)",
            "uri_path": uri_path,
        },
    )


@require_POST
def ping(request):
    return render(request, "partials/ping_result.html", {"ok": True})


def db_ping(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
    except Exception as exc:
        return render(
            request,
            "partials/db_ping_result.html",
            {"ok": False, "error": str(exc)},
            status=500,
        )

    return render(
        request,
        "partials/db_ping_result.html",
        {"ok": True, "result": result},
    )


urlpatterns = [
    # Admin site
    path("admin/", admin.site.urls),
    # Global endpoints
    path("health/", health, name="health"),
    path("db-ping/", db_ping, name="db_ping"),
    path("ping/", ping, name="ping"),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
