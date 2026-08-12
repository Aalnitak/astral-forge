from django import forms

from forgers.models import ForgerProfile
from missions.models import Mission
from rewards.models import Reward


class MissionAssignmentForm(forms.Form):
    forger = forms.ModelChoiceField(
        queryset=ForgerProfile.objects.none(),
        label="Forjador",
    )
    mission = forms.ModelChoiceField(
        queryset=Mission.objects.none(),
        label="Mision",
    )
    starts_on = forms.DateField(
        label="Fecha de inicio",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    ends_on = forms.DateField(
        label="Fecha de termino",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["forger"].queryset = ForgerProfile.objects.order_by(
            "display_name",
            "id",
        )
        self.fields["mission"].queryset = Mission.objects.filter(
            status=Mission.Status.ACTIVE,
        ).order_by("title", "id")


class RewardRedemptionForm(forms.Form):
    forger = forms.ModelChoiceField(
        queryset=ForgerProfile.objects.none(),
        label="Forjador",
    )
    reward = forms.ModelChoiceField(
        queryset=Reward.objects.none(),
        label="Recompensa",
    )
    fulfilled = forms.BooleanField(
        label="Marcar como entregada",
        required=False,
    )
    notes = forms.CharField(
        label="Notas",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["forger"].queryset = ForgerProfile.objects.order_by(
            "display_name",
            "id",
        )
        self.fields["reward"].queryset = Reward.objects.filter(
            status=Reward.Status.ACTIVE,
        ).order_by("title", "id")
