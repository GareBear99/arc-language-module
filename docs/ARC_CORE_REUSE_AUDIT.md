# ARC-Core Reuse Audit

## Good primitives to reuse conceptually
- typed schemas and validation discipline
- SQLite local-first storage
- generic edge storage concepts
- resolver / upsert patterns
- thin API routes

## What required replacement
- entity model was too generic for linguistics
- no script/orthography representation
- no provenance-aware translation assertions
- no lineage confidence / dispute modeling

## Result
ARC-Core is a valid architectural base, but a dedicated language domain model is still required.
