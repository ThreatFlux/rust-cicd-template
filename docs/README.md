# Documentation

<!--
  docs/README.md — What makes this document good:

  This is the index page for the docs/ directory. It gives contributors a
  single entry point to find any document, explains the naming conventions,
  and distinguishes between docs that ship with generated repos vs. docs
  that are specific to this template.

  Best practices:
  - List every file in docs/ with a one-line description.
  - Group files by audience (users, contributors, maintainers).
  - State the naming convention so new docs follow the pattern.
  - Keep this file short — it's a map, not a destination.

  Standard name: docs/README.md
  When to include: Any project with more than two files in docs/.
-->

## Standard Documentation Files

These files follow widely-adopted naming conventions from the Rust ecosystem and GitHub community health standards. Every ThreatFlux project should include the files marked **Essential** and add others as the project matures.

### Root-Level Files

| File | Tier | Audience | Purpose |
|------|------|----------|---------|
| `README.md` | Essential | Everyone | Project overview, badges, quick start, install |
| `LICENSE` | Essential | Everyone | Legal terms (MIT for ThreatFlux projects) |
| `CONTRIBUTING.md` | Essential | Contributors | Dev setup, commit conventions, PR workflow |
| `SECURITY.md` | Essential | Security researchers | Vulnerability reporting process and timeline |
| `CODE_OF_CONDUCT.md` | Essential | Community | Behavior expectations (Contributor Covenant) |
| `README_TEMPLATE.md` | Template-only | Template users | Starter README for generated projects |

### docs/ Directory

| File | Tier | Audience | Purpose |
|------|------|----------|---------|
| [`README.md`](README.md) | Essential | Everyone | This index — entry point for all docs |
| [`README_STANDARDS.md`](README_STANDARDS.md) | Essential | Contributors | README style guide and anti-patterns |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Standard | Contributors | High-level codemap, component boundaries, design decisions |
| [`CHANGELOG.md`](CHANGELOG.md) | Standard | Users | Version history following Keep a Changelog format |
| [`RELEASING.md`](RELEASING.md) | Standard | Maintainers | Release runbook — automated and manual paths |
| [`FAQ.md`](FAQ.md) | Standard | Users | Common questions answered in a searchable flat file |
| [`TEMPLATE_BOOTSTRAP_CHECKLIST.md`](TEMPLATE_BOOTSTRAP_CHECKLIST.md) | Template-only | Template users | Post-generation setup checklist |

## Naming Conventions

| Pattern | Use for | Examples |
|---------|---------|---------|
| `ALLCAPS.md` | Standard community files recognized by GitHub | `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` |
| `Title_Case.md` or `kebab-case.md` | Project-specific guides and references | `README_STANDARDS.md`, `getting-started.md` |

## Adding New Documentation

1. Choose the right tier:
   - **Essential** — every project needs this; missing it is a gap.
   - **Standard** — most mature projects have this; include when the project exceeds ~5k LOC or has multiple contributors.
   - **Situational** — include when a specific need arises (e.g., `MIGRATION.md` for breaking version upgrades, `BENCHMARKS.md` for performance-focused projects, `ECOSYSTEM.md` for frameworks with community extensions).

2. Add an HTML comment block at the top of the new file explaining what makes a good version of that document (see existing files for examples).

3. Update this index.

## Situational Files Reference

These files are not included in the template but are recommended when the situation calls for them:

| File | When to include |
|------|-----------------|
| `MIGRATION.md` | Major version upgrades with breaking changes |
| `BENCHMARKS.md` | Performance is a primary selling point |
| `ROADMAP.md` | Project has formal planning cycles |
| `ECOSYSTEM.md` | Framework or library with community extensions |
| `STYLE.md` | Code style rationale beyond rustfmt/clippy |
| `GOVERNANCE.md` | Multiple maintainers with formal decision process |
| `BREAKING_CHANGES.md` | Frequent breaking changes need a dedicated log |
