# Technical Architecture

This document records the technical decisions for Forja Astral / Astral Forge.
It is the source of truth for intended app structure, domain boundaries, domain
models, and future technical diagrams such as ERDs and flow charts.

This is not a brainstorming document. It should record decisions that are
currently accepted for the project. When decisions change, update this document
with the new direction.

## Product Context

Forja Astral is a Django application for building habits through a symbolic
astral universe.

The core product idea is:

- users complete missions;
- completed missions grant stars;
- completed missions also grant permanent Astral Light;
- stars can be spent on rewards;
- Astral Light never decreases;
- long-term progress unlocks ranks and constellations.

The application should feel calm, minimal, elegant, and persistent. It should
reward effort without relying on punishment, pressure, or excessive competition.

## Current Repository State

The repository currently starts from a minimal Django template.

Current structure:

```text
src/
  manage.py
  core/
  static/
  templates/
```

The `core` package currently owns Django project concerns such as settings,
root URL routing, health checks, and starter views.

Decision: `core` remains infrastructure-focused. Product/domain models live in
separate Django apps.

## Intended Django App Structure

Decision: the project will use domain-oriented Django apps.

Initial app structure:

```text
src/
  core/
  forgers/
  families/
  missions/
  forge/
  rewards/
```

Planned later app structure:

```text
src/
  constellations/
  progression/
```

Decision: `constellations` and `progression` are planned domains, but they will
not be created until their rules are rich enough to justify separate apps. Early
rank or milestone logic may live in `forge`.

## App Responsibilities

### `core`

Project infrastructure.

Responsibilities:

- Django settings;
- root URL configuration;
- health checks;
- shared low-level utilities;
- global middleware or configuration hooks.

Avoid placing product models in `core`.

### `forgers`

User-facing identity and profile domain.

Responsibilities:

- forger profile;
- display name and avatar;
- age group or user type;
- personal preferences;
- user onboarding state;
- possible custom user model decision, if needed early.

### `families`

Family or household relationships.

The manifesto says the application is meant for all ages and that family is a
first-class part of the universe. This app should own group membership and
permission relationships.

Responsibilities:

- family or household records;
- members;
- guardian/child relationships;
- invitations;
- permissions for assigning missions and approving rewards.

### `missions`

Daily actions and repeatable tasks.

Missions are the core activity unit of the application. A mission represents an
action that can be completed by a forger and converted into progress.

Responsibilities:

- mission definitions;
- assigned missions;
- recurring missions;
- mission categories;
- star value;
- completion records;
- notes or proof of completion, if needed later.

### `forge`

Progress economy and permanent effort history.

This is the central app for transforming completed actions into stars, Astral
Light, and long-term progress records.

Responsibilities:

- star balance calculations;
- Astral Light totals;
- earning and spending ledger;
- forge events;
- historical activity timeline;
- rules for converting mission completions into progress.

Decision: progress should be event or ledger based. We should not only store a
mutable "current stars" value. The product promise says rewards can be spent,
but growth remains, so the historical record must be durable.

### `rewards`

Rewards that can be redeemed with stars.

Responsibilities:

- reward catalog;
- reward cost;
- reward availability;
- redemption requests;
- approval flow, especially for family use cases;
- redeemed reward history.

### `constellations`

Long-term milestones and narrative achievements.

Decision: add this app after the core loop is stable. Early constellation logic
may live in `forge` until the milestone rules become rich enough to deserve a
separate app.

Responsibilities:

- constellation definitions;
- unlock criteria;
- discovered constellations;
- user progress toward constellations;
- milestone stories.

### `progression`

Ranks, levels, titles, and experience rules.

Decision: add this app after the core loop is stable. Early rank logic may live
in `forge` if it is just a simple Astral Light threshold.

Responsibilities:

- rank definitions;
- rank thresholds;
- current rank calculation;
- rank unlock history.

Example ranks from the manifesto:

- Aprendiz;
- Explorador;
- Rastreador;
- Cazador;
- Guardian;
- Maestro Astral;
- Forjador Estelar;
- Arquitecto Celeste.

## Domain Model

Decision: the primary domain model is built around forgers completing missions,
earning progress, and redeeming rewards.

Initial domain concepts:

- `ForgerProfile`: the product-facing profile for a Django user.
- `Family`: the single family using the application.
- `FamilyMembership`: relationship between a forger and a family, including
  role and membership status.
- `Mission`: a global task definition.
- `MissionAgeReward`: age-specific availability and reward values for a
  mission.
- `MissionAssignment`: explicit assignment of a mission to a forger.
- `MissionCompletion`: record that a forger completed an assignment.
- `ForgeEvent`: durable event created from meaningful progress actions.
- `StarLedgerEntry`: spendable currency movement.
- `AstralLightLedgerEntry`: permanent progress movement.
- `Reward`: something stars can be redeemed for.
- `RewardRedemption`: record of a reward being requested, redeemed, or
  fulfilled.

Planned later domain concepts:

- `Constellation`: long-term milestone definition.
- `ForgerConstellation`: a constellation discovered by a forger.
- `Rank`: rank or title definition.
- `RankUnlock`: historical record of a rank being reached.

## Core Domain Flow

```text
Forger completes Mission
        |
        v
MissionCompletion creates ForgeEvent
        |
        v
ForgeEvent grants Stars + AstralLight
        |
        v
Stars can be spent on Rewards
        |
        v
AstralLight accumulates forever
        |
        v
Ranks and Constellations unlock from history
```

Decision: mission completion creates historical progress records. Star balance
and Astral Light totals must be traceable back to durable records.

## Modeling Principles

## Implemented Model Decisions

### `forgers.ForgerProfile`

Decision: use Django's configured user model for authentication and create a
separate `ForgerProfile` for product identity.

Fields:

- `user`: one-to-one relationship with `settings.AUTH_USER_MODEL`;
- `display_name`: product-facing name;
- `age_group`: optional classification for child, teen, or adult;
- `is_guardian`: whether the forger can access guardian workflows;
- `created_at`;
- `updated_at`.

Reasoning: this keeps authentication conventional while allowing the application
to use "forger" as its product-facing identity.

Guardian permission is separate from age group. An adult is not automatically a
guardian, and a guardian workflow should check `is_guardian` explicitly.

### `families.Family`

Decision: represent households or groups with a `Family` model.

Fields:

- `name`;
- `created_by`: protected relationship to the creating `ForgerProfile`;
- `created_at`;
- `updated_at`.

Reasoning: families are first-class in the product vision and will later own
mission assignment, reward approval, and guardian/member relationships.

### `families.FamilyMembership`

Decision: represent family participation through an explicit membership model.

Fields:

- `family`;
- `forger`;
- `role`: `guardian` or `member`;
- `status`: `active`, `invited`, or `removed`;
- `joined_at`;
- `updated_at`.

Constraint:

- one membership record per family and forger.

Reasoning: an explicit membership model gives us a stable place to add
permissions, invitations, approval rules, and family-specific settings later.

### `missions.Mission`

Decision: represent reusable global task definitions with a `Mission` model.

The application is intended for one family only, so missions do not need a
family relationship. A mission belongs to the shared mission catalog. If a
forger needs that mission, the mission is assigned through `MissionAssignment`.

Fields:

- `created_by`: forger who created the mission;
- `title`;
- `description`;
- `cadence`: `one_time`, `daily`, or `weekly`;
- `status`: `active` or `archived`;
- `created_at`;
- `updated_at`.

Reasoning: this keeps the first mission model useful as a reusable catalog of
one-time and simple recurring habits without introducing a complex recurrence
engine too early.

### `missions.MissionAgeReward`

Decision: represent mission availability and rewards per age group with a
separate `MissionAgeReward` model.

Fields:

- `mission`;
- `age_group`: `child`, `teen`, or `adult`;
- `star_value`: spendable reward value for that age group;
- `astral_light_value`: permanent progress value for that age group;
- `is_active`;
- `created_at`;
- `updated_at`.

Constraints:

- one reward row per mission and age group;
- `star_value` must be non-negative;
- `astral_light_value` must be non-negative.

Reasoning: the same mission can represent different effort depending on the
forger's age group. A child and an adult can complete the same mission but earn
different stars and different Astral Light. A mission is available to an age
group when it has an active `MissionAgeReward` row for that age group.

### `missions.MissionAssignment`

Decision: assign missions to forgers through a separate `MissionAssignment`
model.

Fields:

- `mission`;
- `forger`: forger who should complete the mission;
- `assigned_by`: forger who assigned the mission;
- `starts_on`;
- `ends_on`;
- `status`: `active`, `paused`, or `archived`;
- `created_at`;
- `updated_at`.

Constraint:

- one active assignment per mission and forger.

Reasoning: this separates the reusable mission definition from the personal
work a forger is expected to complete. One mission can be assigned to many
forgers, and each forger has their own assignment record for that mission. It
also gives the application a clear place to pause, archive, or time-limit
assignments.

### `missions.MissionCompletion`

Decision: represent completed mission instances with a separate
`MissionCompletion` model.

Fields:

- `assignment`;
- `recorded_by`: forger who recorded the completion;
- `completed_at`;
- `completed_on`;
- `status`: `pending`, `approved`, or `rejected`;
- `notes`;
- `created_at`;
- `updated_at`.

Constraint:

- one completion record per assignment and calendar day.

Reasoning: mission completions must be durable records because they are the
input for forge events, star ledger entries, and Astral Light ledger entries.
The status field leaves room for family approval flows without requiring that
approval workflow on day one.

Daily completion check:

```text
Does MissionCompletion exist for this MissionAssignment and today's date?
```

Because `MissionAssignment` already identifies both the mission and the forger,
`MissionCompletion` should point to the assignment instead of duplicating mission
and forger fields.

### `forge.ForgeEvent`

Decision: represent meaningful progress actions with a durable `ForgeEvent`.

Fields:

- `forger`;
- `event_type`: `mission_completed`, `reward_redeemed`, or
  `manual_adjustment`;
- `mission_completion`: optional one-to-one source completion;
- `occurred_at`;
- `notes`;
- `created_at`.

Reasoning: forge events are the narrative and technical bridge between user
actions and ledger entries. A mission completion can create one forge event,
which can then create star and Astral Light ledger entries.

### `forge.StarLedgerEntry`

Decision: represent spendable star balance through signed ledger entries.

Fields:

- `forger`;
- `forge_event`;
- `entry_type`: `earned`, `spent`, or `adjustment`;
- `amount`;
- `created_at`.

Constraint:

- `amount` cannot be zero.

Reasoning: stars are spendable, so the ledger must support both positive and
negative movement. Current star balance should be derived from the sum of a
forger's star ledger entries or cached from that source of truth.

### `forge.AstralLightLedgerEntry`

Decision: represent permanent Astral Light through positive ledger entries.

Fields:

- `forger`;
- `forge_event`;
- `entry_type`: `earned` or `adjustment`;
- `amount`;
- `created_at`.

Constraint:

- `amount` must be positive.

Reasoning: Astral Light represents permanent growth. It can increase, but it
must not be spent or reduced by reward redemption.

### `rewards.Reward`

Decision: represent redeemable rewards with a global `Reward` model.

The application is intended for one family only, so rewards do not need a family
relationship. Rewards belong to the shared reward catalog.

Fields:

- `created_by`: forger who created the reward;
- `title`;
- `description`;
- `star_cost`;
- `requires_approval`;
- `status`: `active` or `archived`;
- `created_at`;
- `updated_at`.

Constraint:

- `star_cost` must be positive.

Reasoning: rewards are the spendable side of the economy. They should be simple
catalog entries that can be requested by any eligible forger.

### `rewards.RewardRedemption`

Decision: represent reward requests and fulfillment with a separate
`RewardRedemption` model.

Fields:

- `reward`;
- `forger`: forger receiving the reward;
- `requested_by`: forger who requested the redemption;
- `approved_by`: guardian who handled the redemption request;
- `forge_event`: optional one-to-one link to the spending event;
- `star_cost`: snapshot of the reward cost at redemption time;
- `status`: `requested`, `redeemed`, `rejected`, `fulfilled`, or `canceled`;
- `requested_at`;
- `resolved_at`;
- `fulfilled_at`;
- `notes`;
- `created_at`;
- `updated_at`.

Constraint:

- `star_cost` must be positive.

Reasoning: redemptions need their own lifecycle because requesting, spending
stars, and fulfilling the reward may happen at different moments.
`redeemed` means stars have been spent. `fulfilled` means the reward has also
been delivered. The redemption stores a star cost snapshot so historical records
remain accurate if the reward catalog changes later.

Reward spending flow:

```text
RewardRedemption redeemed or fulfilled
        |
        v
ForgeEvent(event_type="reward_redeemed")
        |
        v
StarLedgerEntry(amount=-reward_redemption.star_cost)
```

Reward spending must not create an Astral Light ledger entry.

## Service Layer Decisions

Decision: domain workflows that create forge events or ledger entries must go
through `forge.services`.

Reasoning: mission completion and reward redemption both affect multiple
tables. Keeping these workflows in service functions makes it easier to enforce
transactions, validation, balance checks, and ledger consistency.

### `forge.services.complete_mission_assignment`

Decision: completing an assigned mission creates the completion, forge event,
star ledger entry, and Astral Light ledger entry in one database transaction.

Flow:

```text
MissionAssignment
        |
        v
MissionCompletion
        |
        v
ForgeEvent(event_type="mission_completed")
        |
        v
StarLedgerEntry(amount=MissionAgeReward.star_value)
AstralLightLedgerEntry(amount=MissionAgeReward.astral_light_value)
```

Validation:

- the assignment must be active;
- the mission must be active;
- the completion date must be inside the assignment date range;
- the forger must have an age group;
- the mission must have an active `MissionAgeReward` for the forger's age
  group.

Cadence validation:

- `one_time`: the assignment can be completed once total;
- `daily`: the assignment can be completed once per calendar date;
- `weekly`: the assignment can be completed once per ISO-style week, Monday
  through Sunday.

Calendar dates are evaluated in the configured Django timezone. The default
timezone is `America/Santiago`, because recurring family habits should reset on
the family's local day instead of UTC.

Assignment date range:

- `starts_on` and `ends_on` define when an assignment is valid;
- they do not define the recurrence rule;
- recurrence is controlled by `Mission.cadence`.

### `forge.services.assign_mission_to_forger`

Decision: assigning a mission to a forger must go through the service layer.

Flow:

```text
Mission
        |
        v
MissionAssignment(forger)
```

Validation:

- the mission must be active;
- the assigning forger must be a guardian;
- the forger must have an age group;
- the mission must have an active `MissionAgeReward` for the forger's age
  group;
- there must not already be an active assignment for the same mission and
  forger;
- `ends_on`, when present, cannot be before `starts_on`.

Reasoning: invalid assignments should be blocked before completion time. This
keeps the mission catalog, age eligibility rules, and forger assignments aligned.

### `forge.services.request_reward_redemption`

Decision: requesting a reward creates a `RewardRedemption` with a snapshot of
the current reward cost.

Validation:

- the reward must be active.

### `forge.services.redeem_reward`

Decision: redeeming a reward creates the spending forge event and negative star
ledger entry in one database transaction.

Flow:

```text
RewardRedemption
        |
        v
ForgeEvent(event_type="reward_redeemed")
        |
        v
StarLedgerEntry(amount=-RewardRedemption.star_cost)
```

Validation:

- the redemption must not already have spent stars;
- the redemption must be `requested`;
- the forger must have enough available stars.

### `forge.services.reject_reward_redemption`

Decision: rejecting a reward request is also handled by the service layer.

Validation:

- the redemption must be `requested`.

Effects:

- the redemption becomes `rejected`;
- `approved_by` stores the guardian who handled the request;
- `resolved_at` records when the request was rejected;
- no `ForgeEvent` or star ledger entry is created.

### Balance Helpers

Decision: current balances are derived from ledgers.

- `get_star_balance(forger)` sums `StarLedgerEntry.amount`;
- `get_astral_light_total(forger)` sums `AstralLightLedgerEntry.amount`.

## Admin Boundary

Decision: Django admin is an inspection and fallback setup surface, not the main
operational interface.

Editable in admin:

- mission catalog records;
- mission age rewards;
- reward catalog records;
- forger and family setup records.

Read-only in admin:

- mission assignments;
- mission completions;
- forge events;
- star ledger entries;
- Astral Light ledger entries;
- reward redemptions.

Reasoning: assignments, completions, redemptions, forge events, and ledger
entries must be created through service-layer workflows so validation,
transactions, cadence rules, balance checks, and ledger consistency are always
enforced. Guardian UI owns family-facing operational flows.

### Guardian Mission Catalog

Decision: guardians manage the shared mission catalog from dedicated guardian UI
routes.

Routes:

- `/guardian/catalog/missions/`: list catalog missions;
- `/guardian/catalog/missions/new/`: create a mission;
- `/guardian/catalog/missions/<id>/edit/`: edit a mission.

The mission catalog form edits the `Mission` fields and the related
`MissionAgeReward` rows together. A mission can define different star and Astral
Light values for child, teen, and adult forgers. An active mission must have at
least one enabled age group reward.

### Guardian Reward Catalog

Decision: guardians manage the shared reward catalog from dedicated guardian UI
routes.

Routes:

- `/guardian/catalog/rewards/`: list catalog rewards;
- `/guardian/catalog/rewards/new/`: create a reward;
- `/guardian/catalog/rewards/<id>/edit/`: edit a reward.

The reward catalog form edits the `Reward` fields used by future redemption
requests: title, description, star cost, approval requirement, and status.
Existing `RewardRedemption` records keep their own `star_cost` snapshot, so
later catalog edits do not rewrite historical spending records.

### Guardian Family Management

Decision: guardians manage existing forger profiles from dedicated guardian UI
routes.

Routes:

- `/guardian/family/`: list existing forger profiles;
- `/guardian/family/forgers/new/`: create a user, forger profile, and family
  membership;
- `/guardian/family/forgers/<id>/edit/`: edit a forger profile;
- `/guardian/family/forgers/<id>/delete/`: confirm and delete a forger.

Family creation follows the one-family-per-app assumption. Guardians do not pick
a family in the UI. When a new forger is created, the service layer finds the
first `Family` record or creates a default `Familia` record, then attaches the
new forger through `FamilyMembership`. Membership role mirrors
`ForgerProfile.is_guardian`.

Deleting a forger is a destructive guardian workflow with a confirmation page
and POST-only final action. The service deletes the Django user, forger profile,
family membership, assigned missions, mission completions, forge events, ledger
entries, and reward redemptions owned by that forger. Shared catalog records
created by that forger are retained, with nullable creator references cleared.
The service blocks deleting the currently logged-in guardian profile.

### Preserve History

Decision: use durable event or ledger records for meaningful state changes:

- mission completed;
- stars earned;
- stars spent;
- Astral Light gained;
- reward redeemed;
- rank unlocked;
- constellation discovered.

Derived values such as current star balance may be calculated from the ledger or
cached carefully, but the source of truth remains historical.

### Separate Spendable and Permanent Progress

Stars are spendable.

Astral Light is permanent.

Decision: this distinction must appear clearly in the data model. A reward
redemption can reduce available stars, but it must never reduce Astral Light.

### Keep Apps Domain-Oriented

Apps should be split by business responsibility, not by technical layer.

Prefer:

- `missions`
- `forge`
- `rewards`

Avoid:

- `api`
- `views`
- `models`

Decision: shared technical code goes in `core` only when it is genuinely
cross-cutting.

### Start Simple, Leave Room for Growth

The first implementation should support the main loop without overbuilding the
universe.

Build first:

- users/forgers;
- families;
- missions;
- completions;
- star and Astral Light ledger;
- rewards and redemptions.

Add later:

- richer constellation rules;
- rank history;
- advanced recurrence;
- analytics;
- notifications;
- seasonal events.

## Technical Diagrams

This section is reserved for diagrams as the implementation takes shape.

### ERD

Status: pending.

This section should contain the entity relationship diagram for the initial
domain model once models are created.

### Mission Completion Flow

Status: pending.

This section should contain the technical flow from mission completion to
ledger entries, progress updates, and response rendering.

### Reward Redemption Flow

Status: pending.

This section should contain the technical flow for reward redemption, including
approval behavior for family contexts.

### Permission Flow

Status: pending.

This section should contain the authorization model for forgers, family members,
guardians, mission assignment, and reward approval.

## Open Decisions

These decisions still need to be made:

- whether initial rank logic belongs in `forge` or a separate `progression`
  app;
- how detailed mission recurrence should become after the first version;
- whether reward redemption requires guardian approval in all family contexts
  or only for younger members.
