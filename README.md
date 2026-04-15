# ARC Language Module v0.24 (production-track)

A governed, auditable multilingual language/script/lineage substrate.
Separates graph truth from runtime capability, and package-owned data from external corpus dependencies.

---

## What this package actually is

- A **SQLite-backed language graph** — 34 seeded languages across 14 families, with scripts, aliases, lineage edges, phonology profiles, transliteration profiles, pronunciation profiles, and dialect/register/orthography variants.
- A **governed ingestion pipeline** — dry-run mode, conflict detection, dedup reporting, provenance tracking for Glottolog, ISO 639-3, and CLDR corpora.
- A **runtime routing layer** — separates knowing a language from being able to translate or speak it. Every provider gap is surfaced explicitly, never silently.
- An **operator tooling layer** — acquisition workspace, coverage reports, implementation matrix, evidence bundles, conflict review exports, policy controls.
- An **honest gap-tracking system** — every missing corpus is declared in manifests; every unsupported runtime is marked; no fake support.

---

## What this package is not

- A full translation engine — local seeded phrase translation only; Argos/NLLB are optional external dependencies
- A full TTS/speech system — PersonaPlex and similar are boundary stubs
- A complete phonemic inventory — all 34 phonology profiles are broad IPA hints with explicit scope notes
- A character-level transliteration engine — profiles declare the scheme and maturity; character mapping tables are not bundled

---

## Quick start

```bash
pip install -e .

python -m arc_lang.cli.main init-db
python -m arc_lang.cli.main seed-common-languages
python -m arc_lang.cli.main stats
python -m arc_lang.cli.main coverage-report
python -m arc_lang.cli.main system-status
python -m arc_lang.cli.main build-implementation-matrix
```

---

## Seed coverage (v0.24)

| Surface | Count | Notes |
|---------|-------|-------|
| Languages | 34 | Across 14 families |
| Families / branches (lineage nodes) | 33 | |
| Scripts | 15 | Latn, Cyrl, Arab, Deva, Beng, Guru, Taml, Telu, Thai, Hira/Kana, Kore, Hans/Hant, Hebr, Ethi, Cher, Grek |
| Language aliases | 77 | Endonyms, exonyms, romanized forms |
| Phonology profiles | 34 | All 34 seeded languages — broad IPA hints |
| Transliteration profiles | 21 | All non-Latin-script languages |
| Pronunciation profiles | 34 | All 34 seeded languages |
| Language variants | 37 | Dialects, registers, orthographies, historical stages |
| Phrase translations | 71 | Common phrases across all 34 languages |
| Provider registry | 10 | local + optional stubs |
| Language capabilities | 238 | Maturity-tracked per language per capability |

All 34 seeded languages have zero missing-profile flags in coverage reports. Transliteration profiles are only required for non-Latin-script languages — Latin-script languages correctly report `missing_transliteration: false`.

---

## Ingestion (dry-run safe)

```bash
# Preview — no writes, shows conflicts
python -m arc_lang.cli.main import-glottolog-fixture path/to/glottolog.csv --dry-run

# Live — idempotent, provenance-tracked, dedup-reported
python -m arc_lang.cli.main import-glottolog-fixture path/to/glottolog.csv
python -m arc_lang.cli.main import-iso-fixture path/to/iso639-3.csv
python -m arc_lang.cli.main import-cldr-fixture path/to/cldr.json
```

Live imports report: `records_seen`, `records_inserted`, `records_updated`, `conflict_count`. Conflicts against existing custom lineage assertions are surfaced in the return payload — never silently overwritten.

---

## Phonology

All 34 languages have seeded broad IPA phonology profiles including: stress policy, syllable template, IPA examples. Low-resource languages (Navajo, Cherokee, Plains Cree) include explicit notes directing operators to authoritative community resources.

```bash
python -m arc_lang.cli.main phonology-hint "こんにちは" lang:jpn
python -m arc_lang.cli.main list-phonology-profiles --language-id lang:arb
python -m arc_lang.cli.main upsert-phonology-profile lang:ita narrow_ipa --broad-ipa "itaˈljano"
```

---

## Transliteration

21 entries covering all non-Latin-script languages in the seed. Each profile declares its scheme name and coverage maturity (`seeded | experimental | reviewed | production`).

```bash
python -m arc_lang.cli.main list-transliteration-profiles --language-id lang:jpn
python -m arc_lang.cli.main transliterate "привет" Cyrl Latn
```

---

## Language variants

37 dialect, register, orthography, and historical-stage variants seeded for 12 languages.

```bash
python -m arc_lang.cli.main list-language-variants --language-id lang:eng
python -m arc_lang.cli.main list-language-variants --variant-type historical_stage
python -m arc_lang.cli.main upsert-language-variant lang:deu "Bavarian" dialect --region-hint DE-BY --mutual-intelligibility 0.7
```

---

## Arbitration

Source-weight-aware lineage arbitration reads live DB weights — operator changes via `set-source-weight` take effect immediately:

```bash
python -m arc_lang.cli.main set-source-weight glottolog 1.0
python -m arc_lang.cli.main effective-lineage lang:spa
python -m arc_lang.cli.main export-conflict-review conflicts.json
```

Scoring: `confidence × source_weight(DB) × status_weight × decision_weight × dispute_factor`. Canonical edges score with `status_weight=1.0`; disputed custom assertions score at `0.45`.

---

## Coverage reporting

```bash
python -m arc_lang.cli.main coverage-report
python -m arc_lang.cli.main coverage-report --language-id lang:jpn --language-id lang:kor --output-path cov.json
```

Per-language output includes: alias count by type, script count, phonology/transliteration/pronunciation profile counts, lineage edge count, custom lineage count, capability maturity summary, and 4 honest gap flags. Summary includes aggregate gap counts.

---

## Acquisition workspace

```bash
python -m arc_lang.cli.main plan-acquisition-job Glottolog --stage-name staging
python -m arc_lang.cli.main record-staged-asset <job_id> /path/to/file.csv
python -m arc_lang.cli.main validate-staged-asset /path/to/file.csv csv
python -m arc_lang.cli.main export-ingestion-workspace workspace.json
```

---

## External dependencies (not bundled)

| Provider | Enables | How to activate |
|----------|---------|-----------------|
| `argostranslate` | Local neural MT | `pip install argostranslate` + model download |
| NLLB | Large-scale neural MT | External inference server (bridge stub) |
| PersonaPlex | Neural speech synthesis | NVIDIA API (boundary stub) |
| Glottolog corpus | Real genealogy data | Download from glottolog.org |
| ISO 639-3 corpus | Authoritative identifiers | Download from SIL |
| CLDR corpus | Script/locale mappings | Download from unicode.org |

---

## Architecture

See `docs/ARCHITECTURE.md` for: separation of concerns table, arbitration formula, provider model, complete data-flow diagram, and 39-table schema inventory.

See `docs/INGESTION_PLAN.md` for: dry-run semantics, dedup reporting, conflict detection, import order, source authority weights.

See `docs/IMPLEMENTATION_MANIFESTS_AND_PHONOLOGY.md` for: honest surface-by-surface implementation status, phonology scope statement, transliteration scheme table.

---

## Tests

```bash
python -m pytest tests/ -q
# 325 tests, 0 failures
```

28 test files covering: smoke, importers (dry_run + conflict detection), governance, arbitration (DB source weights), search (alias table), coverage report (gap flags), phonology, transliteration, pronunciation, variants, acquisition workspace, implementation matrix, batch I/O, provider runtime, evidence export, policy, and seed completeness.
