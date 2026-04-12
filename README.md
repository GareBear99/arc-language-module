# ARC Language Module v0.13.0

A text-first multilingual language/script/lineage substrate for ARC-style systems.

## What v0.6 adds
- lineage normalized into real family/branch nodes
- lineage node provenance
- seeded lexeme + etymology layer
- translate/explain now returns etymology when available
- optional PersonaPlex speech boundary remains downstream only

## Quick start
```bash
python -m arc_lang.cli.main init-db
python -m arc_lang.cli.main seed-common-languages
python -m arc_lang.cli.main detect "hola gracias"
python -m arc_lang.cli.main lineage lang:spa
python -m arc_lang.cli.main etymology lang:ita ciao
python -m arc_lang.cli.main translate-explain hola lang:eng
```


## Language onboarding

You can now add new languages through a staged submission flow instead of raw database edits. This supports review, approval, and promotion into the canonical graph, plus separate custom lineage assertions for disputed or incomplete classifications.


## v10 additions

- Source arbitration for lineage conflicts
- Effective truth view that compares canonical lineage edges, custom assertions, and review decisions
- Conflict surfacing instead of silent flattening
- New CLI command: `arc-lang effective-lineage <language_id>`
- New API route: `GET /lineage/{language_id}/effective`


## Runtime orchestration

Version 0.10.0 adds provider-aware runtime routing for translation and speech. The module now separates graph truth from execution routing, so requests can be gated by per-language capability maturity before they are sent to a translation or speech provider.

New CLI examples:

- `arc-lang runtime-translate hola lang:eng --require-speech --speech-provider personaplex`
- `arc-lang runtime-speak hello lang:eng --provider personaplex`

New API routes:

- `POST /runtime/translate`
- `POST /runtime/speak`


## v12 additions

- Provider registry with enable/disable and local-only flags
- Provider health snapshots (healthy/degraded/offline)
- Runtime job receipts for translation and speech execution
- Health-aware runtime orchestration that blocks offline providers


## v13 additions

- Built-in translation backend adapter framework
- Working local backends for seeded graph translation and same-language mirror routing
- Boundary stubs for future Argos/NLLB style adapters
- New API route: `GET /providers/translation-backends`
- New CLI command: `arc-lang list-translation-backends`
- Runtime translation now routes through adapters instead of hard-coded local-only fallbacks


## New in v14

- Added `argos_local` as an optional offline translation backend boundary with honest dependency/package checks.
- Keeps translation runtime auditable through the existing registry, health, and receipt system.


## v15 runtime diagnostics

This version adds provider diagnostics, Argos local installed-package inspection, per-language-pair translation readiness, and a readiness matrix so the runtime can explain exactly what is executable locally versus only theoretically wired.


## New in v0.16.0
- translation install-plan generation for provider/language pairs
- install-plan recording and listing in SQLite
- actionable package/configuration next steps for argos_local and boundary providers
- package lifecycle documentation in `docs/PACKAGE_LIFECYCLE.md`


## v17 additions

- provider action catalog for runtime/install workflows
- dry-run/apply provider action execution
- provider action receipts for auditable backend lifecycle steps


## v18 Hardening Additions

- system status summary
- operator policy controls
- evidence bundle export
- policy-aware runtime and provider action blocking


## New in v19

- pronunciation hint profiles
- morphology/syntax assist analysis
- translate-explain now carries source analysis and target pronunciation hints
- system status includes pronunciation profile coverage


## v20 highlights

- Transliteration profiles and profile-aware transliteration routing
- Better low-resource maturity defaults for Navajo, Cherokee, and Plains Cree
- Richer operator status with readiness summary
- Analysis output now includes transliteration profile context


## v22 growth surfaces

- semantic concept graphing
- dialect/register/orthography variant metadata
- conflict review bundle export
- per-language coverage reporting


## New in v23

- Phonology profile scaffolding with broad IPA hints
- Backend manifests describing runtime and bridge expectations
- Corpus manifests separating installed seed data from external required datasets
- Implementation matrix reports that split package-owned features from external-data/runtime dependencies


## v24 acquisition and validation layer

This build adds an acquisition workspace for external corpora and real-source ingestion. It can plan corpus staging jobs, record staged assets, validate local source files before import, and export an operator-facing ingestion workspace bundle. This closes the package-owned gap between **manifest says external data is needed** and **operator has a governed path to acquire, stage, validate, and track that data**.
