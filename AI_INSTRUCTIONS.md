# AI Instructions

These instructions are project-level context for every AI-assisted chat about this repository.

## Language

The main working language for conversations is English.

Inside the application itself, Spanish is the default user-facing language. UI labels, messages, empty states, onboarding text, notifications, and product copy should be written in Spanish unless explicitly requested otherwise.

Translation and multi-language support can be added later, but Spanish should be treated as the product's default language for now.

## Required Project Context

Always treat these root files as part of the working context:

- `AI_INSTRUCTIONS.md`
- `APP_MANIFEST.md`

Use `APP_MANIFEST.md` to preserve the product's identity, philosophy, tone, and visual direction.

## Product Principles

Forja Astral should feel calm, meaningful, and encouraging.

Favor progress, consistency, and personal growth over pressure, punishment, streak anxiety, or excessive competition.

Completed tasks should feel like small acts of construction in the user's personal firmament.

The interface should feel minimal, elegant, celestial, and quiet, with Spanish copy that is warm and clear.

## Permission Rules

Use a practical permission approach.

Reading files and inspecting the project structure is allowed without asking unless the user says otherwise.

Before running commands that execute code, modify files, install dependencies, start services, use the network, change git state, or perform destructive actions, ask the user first.

## Engineering Preferences

Prefer existing project patterns before introducing new abstractions.

Keep changes scoped to the user's request.

Avoid unrelated refactors.

Use English for all code-level naming, including variables, functions, classes, methods, files, database fields, API identifiers, comments, and tests.

Use Spanish only for user-facing application text unless explicitly requested otherwise.

When building UI, prioritize real app screens and workflows over marketing-style landing pages.

When editing user-facing text, write it in Spanish by default.

## Version-Aware Documentation

Use the Python version and dependency versions defined by this application.

When researching framework, library, or tooling behavior, use documentation that matches the version used by the project. For example, if the app uses Django `x.y`, consult the Django `x.y` documentation instead of the latest documentation by default.

If the installed or pinned version is unclear, inspect the project configuration before assuming a version.
