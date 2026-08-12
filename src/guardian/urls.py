from django.urls import path

from . import views

app_name = "guardian"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("missions/", views.missions, name="missions"),
    path("rewards/", views.rewards, name="rewards"),
    path("assign-mission/", views.assign_mission, name="assign_mission"),
    path("redeem-reward/", views.redeem_reward_view, name="redeem_reward"),
    path(
        "assignments/<int:assignment_id>/complete/",
        views.complete_assignment,
        name="complete_assignment",
    ),
    path(
        "redemptions/<int:redemption_id>/fulfill/",
        views.fulfill_redemption,
        name="fulfill_redemption",
    ),
    path(
        "redemptions/<int:redemption_id>/redeem/",
        views.redeem_redemption,
        name="redeem_redemption",
    ),
    path(
        "redemptions/<int:redemption_id>/reject/",
        views.reject_redemption,
        name="reject_redemption",
    ),
]
