# Architecture

## Core layers

1. Identity layer
   - family, branch, language, dialect, macrolanguage
2. Script layer
   - script, orthography, transliteration system
3. Lineage layer
   - genealogical descent, dialect-of, disputed branch, borrowed-from
4. Lexeme / assertion layer
   - translation claims, pronunciation hints, etymology, provenance
5. Optional speech layer
   - native-language playback adapter

## Storage pattern

SQLite is used for a portable local-first canonical store.

Tables:
- languages
- scripts
- language_scripts
- lineage_edges
- translation_assertions
- provenance_records

## Detection pipeline

1. Unicode/script hints
2. stopword and character profile scoring
3. seed alias matching
4. tie-break confidence shaping
5. fallback to unknown

## Speech architecture

Speech output is deliberately downstream:
- detect / normalize text
- resolve target language
- translate / explain
- optionally invoke speech provider

PersonaPlex belongs only at the final optional stage.
