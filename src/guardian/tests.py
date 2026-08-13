from django.contrib.auth import get_user_model
from django.test import TestCase

from forgers.models import ForgerProfile
from guardian.forms import ForgerCreationForm
from guardian.forms import ForgerProfileForm
from guardian.forms import MissionCatalogForm
from guardian.forms import RewardCatalogForm
from missions.models import Mission
from missions.models import MissionAgeReward
from rewards.models import Reward


class ForgerProfileFormTests(TestCase):
    def test_forger_creation_form_rejects_duplicate_username(self):
        get_user_model().objects.create_user(username="nova")
        form = ForgerCreationForm(
            data={
                "username": "nova",
                "password": "secret-pass",
                "password_confirm": "secret-pass",
                "display_name": "Nova",
                "age_group": ForgerProfile.AgeGroup.CHILD,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_forger_creation_form_requires_matching_passwords(self):
        form = ForgerCreationForm(
            data={
                "username": "nova",
                "password": "secret-pass",
                "password_confirm": "different-pass",
                "display_name": "Nova",
                "age_group": ForgerProfile.AgeGroup.CHILD,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Las contrasenas no coinciden.", form.non_field_errors())

    def test_forger_profile_form_updates_profile_fields(self):
        user = get_user_model().objects.create_user(username="nova")
        forger = ForgerProfile.objects.create(
            user=user,
            display_name="Nova",
            age_group=ForgerProfile.AgeGroup.CHILD,
        )
        form = ForgerProfileForm(
            data={
                "display_name": "Nova Mayor",
                "age_group": ForgerProfile.AgeGroup.TEEN,
                "is_guardian": "on",
            },
            instance=forger,
        )

        self.assertTrue(form.is_valid())
        updated = form.save()

        self.assertEqual(updated.display_name, "Nova Mayor")
        self.assertEqual(updated.age_group, ForgerProfile.AgeGroup.TEEN)
        self.assertTrue(updated.is_guardian)


class MissionCatalogFormTests(TestCase):
    def form_data(self, **overrides):
        data = {
            "title": "Ordenar dormitorio",
            "description": "Dejar el dormitorio listo antes de dormir.",
            "cadence": Mission.Cadence.DAILY,
            "status": Mission.Status.ACTIVE,
            "child_enabled": "on",
            "child_star_value": "3",
            "child_astral_light_value": "2",
            "teen_star_value": "4",
            "teen_astral_light_value": "2",
            "adult_star_value": "1",
            "adult_astral_light_value": "1",
        }
        data.update(overrides)
        return data

    def test_active_mission_requires_enabled_age_group(self):
        data = self.form_data()
        data.pop("child_enabled")
        form = MissionCatalogForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Una mision activa necesita al menos un grupo de edad habilitado.",
            form.non_field_errors(),
        )

    def test_save_age_rewards_creates_values_for_each_age_group(self):
        form = MissionCatalogForm(data=self.form_data())

        self.assertTrue(form.is_valid())
        mission = form.save()
        form.save_age_rewards(mission)

        self.assertEqual(mission.title, "Ordenar dormitorio")
        self.assertEqual(MissionAgeReward.objects.count(), 3)

        child_reward = MissionAgeReward.objects.get(
            mission=mission,
            age_group=MissionAgeReward.AgeGroup.CHILD,
        )
        teen_reward = MissionAgeReward.objects.get(
            mission=mission,
            age_group=MissionAgeReward.AgeGroup.TEEN,
        )

        self.assertTrue(child_reward.is_active)
        self.assertEqual(child_reward.star_value, 3)
        self.assertEqual(child_reward.astral_light_value, 2)
        self.assertFalse(teen_reward.is_active)


class RewardCatalogFormTests(TestCase):
    def test_reward_catalog_form_saves_reward(self):
        form = RewardCatalogForm(
            data={
                "title": "Noche de pelicula",
                "description": "Elegir una pelicula familiar.",
                "star_cost": "8",
                "requires_approval": "on",
                "status": Reward.Status.ACTIVE,
            }
        )

        self.assertTrue(form.is_valid())
        reward = form.save()

        self.assertEqual(reward.title, "Noche de pelicula")
        self.assertEqual(reward.star_cost, 8)
        self.assertTrue(reward.requires_approval)
        self.assertEqual(reward.status, Reward.Status.ACTIVE)

    def test_reward_catalog_form_requires_positive_star_cost(self):
        form = RewardCatalogForm(
            data={
                "title": "Costo invalido",
                "description": "",
                "star_cost": "0",
                "status": Reward.Status.ACTIVE,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("star_cost", form.errors)
