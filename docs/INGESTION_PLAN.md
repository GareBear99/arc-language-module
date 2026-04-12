# Ingestion Plan v5

This build moves the package past seed-only mode by adding file-based importers and source manifests.

## Ingestion doctrine
- Glottolog-like inputs populate genealogical structure.
- ISO 639-3-like inputs normalize identifiers and aliases.
- CLDR-like inputs populate script support and display aliases.
- No source is treated as universal truth for every field.
- Provenance is attached to every imported record.

## Supported file formats in v5
- CSV for Glottolog-style and ISO-style imports
- JSON for CLDR-style imports

## Import order
1. Initialize DB
2. Seed common bootstrap data
3. Import Glottolog-style genealogy rows
4. Import ISO 639-3-style alias/code rows
5. Import CLDR-style script mappings

## Why this matters
This package can now move from a hand-seeded demo into a source-aware language graph, while preserving uncertainty and provenance.
