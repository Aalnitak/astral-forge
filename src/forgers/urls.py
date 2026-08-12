from django.urls import path

from . import views

app_name = "forgers"

urlpatterns = [
    path("me/rewards/", views.rewards, name="rewards"),
    path(
        "me/rewards/<int:reward_id>/request/",
        views.request_reward,
        name="request_reward",
    ),
    path("me/", views.me, name="me"),
    path("<str:username>/", views.profile, name="profile"),
    path(
        "assignments/<int:assignment_id>/complete/",
        views.complete_assignment,
        name="complete_assignment",
    ),
]
