from django.urls import path

from . import views

app_name = "guardian"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("family/", views.family, name="family"),
    path("family/forgers/new/", views.forger_create, name="forger_create"),
    path(
        "family/forgers/<int:forger_id>/edit/",
        views.forger_edit,
        name="forger_edit",
    ),
    path(
        "family/forgers/<int:forger_id>/delete/",
        views.forger_delete,
        name="forger_delete",
    ),
    path("missions/", views.missions, name="missions"),
    path("catalog/missions/", views.mission_catalog, name="mission_catalog"),
    path("catalog/missions/new/", views.mission_create, name="mission_create"),
    path(
        "catalog/missions/<int:mission_id>/edit/",
        views.mission_edit,
        name="mission_edit",
    ),
    path("rewards/", views.rewards, name="rewards"),
    path("catalog/rewards/", views.reward_catalog, name="reward_catalog"),
    path("catalog/rewards/new/", views.reward_create, name="reward_create"),
    path(
        "catalog/rewards/<int:reward_id>/edit/",
        views.reward_edit,
        name="reward_edit",
    ),
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
