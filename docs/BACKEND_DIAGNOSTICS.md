# Backend Diagnostics

This version adds runtime diagnostics for translation backends and provider health.

## Goals
- Inspect whether optional local dependencies are present
- Inspect installed local translation packages where possible
- Report translation readiness for a specific source/target pair
- Generate a readiness matrix across translation-capable languages

## Current provider-specific behavior

### `argos_local`
- Checks whether `argostranslate` is importable
- Lists installed runtime language codes
- Lists installed source→target translation pairs
- Marks readiness as `ready`, `degraded`, or `blocked`

### Boundary stubs
Providers like `argos_bridge` and `nllb_bridge` can be health-checked and capability-gated, but they remain `theoretical` until a live bridge is implemented.

## API
- `GET /providers/diagnostics`
- `GET /runtime/readiness/translation`
- `GET /runtime/readiness/matrix`

## CLI
- `arc-lang provider-diagnostics [provider_name]`
- `arc-lang translation-readiness <source_language_id> <target_language_id> [--provider name]`
- `arc-lang translation-readiness-matrix [--target-language-id id] [--provider name] [--limit N]`
