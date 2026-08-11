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

- `Forger`: the product-facing profile for a user.
- `Family`: a group or household containing multiple forgers.
- `FamilyMembership`: relationship between a forger and a family, including
  role or permissions.
- `Mission`: a task or activity that can be assigned and completed.
- `MissionCompletion`: record that a forger completed a mission.
- `ForgeEvent`: durable event created from meaningful progress actions.
- `StarLedgerEntry`: spendable currency movement.
- `AstralLightLedgerEntry`: permanent progress movement.
- `Reward`: something stars can be redeemed for.
- `RewardRedemption`: record of a reward being requested, approved, or redeemed.

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

- whether to use Django's default `User` model or define a custom user model
  early;
- whether `forgers` should be named `accounts` for convention or kept as
  `forgers` for domain clarity;
- whether initial rank logic belongs in `forge` or a separate `progression`
  app;
- how detailed mission recurrence should be in the first version;
- whether reward redemption requires guardian approval in all family contexts
  or only for younger members.
