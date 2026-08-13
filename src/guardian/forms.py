from django import forms
from django.contrib.auth import get_user_model

from forgers.models import ForgerProfile
from missions.models import Mission
from missions.models import MissionAgeReward
from rewards.models import Reward


class ForgerProfileForm(forms.ModelForm):
    class Meta:
        model = ForgerProfile
        fields = ["display_name", "age_group", "is_guardian"]
        labels = {
            "display_name": "Nombre visible",
            "age_group": "Grupo de edad",
            "is_guardian": "Es guardian",
        }


class ForgerCreationForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput,
    )
    password_confirm = forms.CharField(
        label="Confirmar contrasena",
        widget=forms.PasswordInput,
    )
    display_name = forms.CharField(label="Nombre visible", max_length=80)
    age_group = forms.ChoiceField(
        label="Grupo de edad",
        choices=[("", "Sin grupo de edad"), *ForgerProfile.AgeGroup.choices],
        required=False,
    )
    is_guardian = forms.BooleanField(label="Es guardian", required=False)

    def clean_username(self):
        username = self.cleaned_data["username"]

        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("Ya existe un usuario con este nombre.")

        return username

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            raise forms.ValidationError("Las contrasenas no coinciden.")

        return cleaned_data


class RewardCatalogForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ["title", "description", "star_cost", "requires_approval", "status"]
        labels = {
            "title": "Titulo",
            "description": "Descripcion",
            "star_cost": "Costo en estrellas",
            "requires_approval": "Requiere aprobacion",
            "status": "Estado",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class MissionCatalogForm(forms.ModelForm):
    age_groups = ForgerProfile.AgeGroup.choices

    class Meta:
        model = Mission
        fields = ["title", "description", "cadence", "status"]
        labels = {
            "title": "Titulo",
            "description": "Descripcion",
            "cadence": "Recurrencia",
            "status": "Estado",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reward_by_age_group = {}

        if self.instance and self.instance.pk:
            reward_by_age_group = {
                reward.age_group: reward
                for reward in self.instance.age_rewards.all()
            }

        for age_group, label in self.age_groups:
            reward = reward_by_age_group.get(age_group)
            self.fields[f"{age_group}_enabled"] = forms.BooleanField(
                label=label,
                required=False,
                initial=reward.is_active if reward else True,
            )
            self.fields[f"{age_group}_star_value"] = forms.IntegerField(
                label="Estrellas",
                min_value=0,
                initial=reward.star_value if reward else 1,
            )
            self.fields[f"{age_group}_astral_light_value"] = forms.IntegerField(
                label="Luz Astral",
                min_value=0,
                initial=reward.astral_light_value if reward else 1,
            )

    def clean(self):
        cleaned_data = super().clean()
        enabled_age_groups = [
            age_group
            for age_group, _label in self.age_groups
            if cleaned_data.get(f"{age_group}_enabled")
        ]

        if cleaned_data.get("status") == Mission.Status.ACTIVE and not enabled_age_groups:
            raise forms.ValidationError(
                "Una mision activa necesita al menos un grupo de edad habilitado."
            )

        return cleaned_data

    def age_reward_rows(self):
        for age_group, label in self.age_groups:
            yield {
                "age_group": age_group,
                "label": label,
                "enabled": self[f"{age_group}_enabled"],
                "star_value": self[f"{age_group}_star_value"],
                "astral_light_value": self[f"{age_group}_astral_light_value"],
            }

    def save_age_rewards(self, mission):
        for age_group, _label in self.age_groups:
            MissionAgeReward.objects.update_or_create(
                mission=mission,
                age_group=age_group,
                defaults={
                    "is_active": self.cleaned_data[f"{age_group}_enabled"],
                    "star_value": self.cleaned_data[f"{age_group}_star_value"],
                    "astral_light_value": self.cleaned_data[
                        f"{age_group}_astral_light_value"
                    ],
                },
            )


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
