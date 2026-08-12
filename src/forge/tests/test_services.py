from datetime import date
from datetime import datetime
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from forge.models import AstralLightLedgerEntry
from forge.models import ForgeEvent
from forge.models import StarLedgerEntry
from forge.services import assign_mission_to_forger
from forge.services import complete_mission_assignment
from forge.services import get_astral_light_total
from forge.services import get_star_balance
from forge.services import redeem_reward
from forge.services import request_reward_redemption
from forgers.models import ForgerProfile
from missions.models import Mission
from missions.models import MissionAgeReward
from missions.models import MissionAssignment
from missions.models import MissionCompletion
from rewards.models import Reward
from rewards.models import RewardRedemption


class ForgeServiceTests(TestCase):
    def setUp(self):
        self.guardian = self.create_forger(
            username="guardian",
            display_name="Guardian",
            age_group=ForgerProfile.AgeGroup.ADULT,
        )
        self.child = self.create_forger(
            username="child",
            display_name="Child",
            age_group=ForgerProfile.AgeGroup.CHILD,
        )

    def create_forger(self, username, display_name, age_group):
        user = get_user_model().objects.create_user(username=username)
        return ForgerProfile.objects.create(
            user=user,
            display_name=display_name,
            age_group=age_group,
        )

    def create_assignment(
        self,
        cadence=Mission.Cadence.DAILY,
        child_stars=5,
        child_light=3,
        forger=None,
    ):
        mission = Mission.objects.create(
            created_by=self.guardian,
            title=f"{cadence} mission",
            cadence=cadence,
        )
        MissionAgeReward.objects.create(
            mission=mission,
            age_group=ForgerProfile.AgeGroup.CHILD,
            star_value=child_stars,
            astral_light_value=child_light,
        )
        return MissionAssignment.objects.create(
            mission=mission,
            forger=forger or self.child,
            assigned_by=self.guardian,
            starts_on=date(2026, 8, 1),
        )

    def create_mission_with_child_reward(self, status=Mission.Status.ACTIVE):
        mission = Mission.objects.create(
            created_by=self.guardian,
            title="Assignable mission",
            cadence=Mission.Cadence.DAILY,
            status=status,
        )
        MissionAgeReward.objects.create(
            mission=mission,
            age_group=ForgerProfile.AgeGroup.CHILD,
            star_value=5,
            astral_light_value=3,
        )
        return mission

    def test_assign_mission_to_forger_creates_assignment(self):
        mission = self.create_mission_with_child_reward()

        assignment = assign_mission_to_forger(
            mission=mission,
            forger=self.child,
            assigned_by=self.guardian,
            starts_on=date(2026, 8, 11),
        )

        self.assertEqual(assignment.mission, mission)
        self.assertEqual(assignment.forger, self.child)
        self.assertEqual(assignment.assigned_by, self.guardian)
        self.assertEqual(assignment.starts_on, date(2026, 8, 11))

    def test_assign_mission_requires_active_mission(self):
        mission = self.create_mission_with_child_reward(status=Mission.Status.ARCHIVED)

        with self.assertRaises(ValidationError):
            assign_mission_to_forger(
                mission=mission,
                forger=self.child,
                assigned_by=self.guardian,
            )

    def test_assign_mission_requires_age_reward(self):
        mission = self.create_mission_with_child_reward()

        with self.assertRaises(ValidationError):
            assign_mission_to_forger(
                mission=mission,
                forger=self.guardian,
                assigned_by=self.guardian,
            )

    def test_assign_mission_blocks_duplicate_active_assignment(self):
        mission = self.create_mission_with_child_reward()
        assign_mission_to_forger(
            mission=mission,
            forger=self.child,
            assigned_by=self.guardian,
        )

        with self.assertRaises(ValidationError):
            assign_mission_to_forger(
                mission=mission,
                forger=self.child,
                assigned_by=self.guardian,
            )

    def test_assign_mission_requires_valid_date_window(self):
        mission = self.create_mission_with_child_reward()

        with self.assertRaises(ValidationError):
            assign_mission_to_forger(
                mission=mission,
                forger=self.child,
                assigned_by=self.guardian,
                starts_on=date(2026, 8, 11),
                ends_on=date(2026, 8, 10),
            )

    def test_complete_mission_assignment_creates_progress_records(self):
        assignment = self.create_assignment(child_stars=7, child_light=4)
        completed_at = timezone.make_aware(datetime(2026, 8, 11, 10, 30))

        completion = complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=completed_at,
        )

        self.assertEqual(MissionCompletion.objects.count(), 1)
        self.assertEqual(ForgeEvent.objects.count(), 1)
        self.assertEqual(StarLedgerEntry.objects.count(), 1)
        self.assertEqual(AstralLightLedgerEntry.objects.count(), 1)
        self.assertEqual(completion.assignment, assignment)
        self.assertEqual(get_star_balance(self.child), 7)
        self.assertEqual(get_astral_light_total(self.child), 4)

    def test_daily_mission_cannot_be_completed_twice_on_same_day(self):
        assignment = self.create_assignment(cadence=Mission.Cadence.DAILY)
        completed_at = timezone.make_aware(datetime(2026, 8, 11, 9, 0))

        complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=completed_at,
        )

        with self.assertRaises(ValidationError):
            complete_mission_assignment(
                assignment=assignment,
                recorded_by=self.child,
                completed_at=completed_at + timedelta(hours=1),
            )

    def test_one_time_mission_can_only_be_completed_once(self):
        assignment = self.create_assignment(cadence=Mission.Cadence.ONE_TIME)
        completed_at = timezone.make_aware(datetime(2026, 8, 11, 9, 0))

        complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=completed_at,
        )

        with self.assertRaises(ValidationError):
            complete_mission_assignment(
                assignment=assignment,
                recorded_by=self.child,
                completed_at=completed_at + timedelta(days=1),
            )

    def test_weekly_mission_can_only_be_completed_once_per_week(self):
        assignment = self.create_assignment(cadence=Mission.Cadence.WEEKLY)
        monday = timezone.make_aware(datetime(2026, 8, 10, 9, 0))

        complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=monday,
        )

        with self.assertRaises(ValidationError):
            complete_mission_assignment(
                assignment=assignment,
                recorded_by=self.child,
                completed_at=monday + timedelta(days=2),
            )

        next_week_completion = complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=monday + timedelta(days=7),
        )

        self.assertEqual(next_week_completion.completed_on, date(2026, 8, 17))

    def test_missing_age_reward_blocks_mission_completion(self):
        adult_assignment = self.create_assignment(forger=self.guardian)
        completed_at = timezone.make_aware(datetime(2026, 8, 11, 9, 0))

        with self.assertRaises(ValidationError):
            complete_mission_assignment(
                assignment=adult_assignment,
                recorded_by=self.guardian,
                completed_at=completed_at,
            )

    def test_redeem_reward_spends_stars_without_changing_astral_light(self):
        assignment = self.create_assignment(child_stars=10, child_light=6)
        completed_at = timezone.make_aware(datetime(2026, 8, 11, 9, 0))
        complete_mission_assignment(
            assignment=assignment,
            recorded_by=self.child,
            completed_at=completed_at,
        )
        reward = Reward.objects.create(
            created_by=self.guardian,
            title="Screen time",
            star_cost=4,
        )
        redemption = request_reward_redemption(
            reward=reward,
            forger=self.child,
            requested_by=self.child,
        )

        redeemed = redeem_reward(redemption=redemption, approved_by=self.guardian)

        self.assertEqual(redeemed.status, RewardRedemption.Status.APPROVED)
        self.assertEqual(get_star_balance(self.child), 6)
        self.assertEqual(get_astral_light_total(self.child), 6)
        self.assertEqual(
            StarLedgerEntry.objects.filter(
                entry_type=StarLedgerEntry.EntryType.SPENT
            ).count(),
            1,
        )
        self.assertFalse(
            AstralLightLedgerEntry.objects.filter(
                forge_event=redeemed.forge_event
            ).exists()
        )

    def test_redeem_reward_requires_enough_stars(self):
        reward = Reward.objects.create(
            created_by=self.guardian,
            title="Movie night",
            star_cost=5,
        )
        redemption = request_reward_redemption(
            reward=reward,
            forger=self.child,
            requested_by=self.child,
        )

        with self.assertRaises(ValidationError):
            redeem_reward(redemption=redemption, approved_by=self.guardian)
