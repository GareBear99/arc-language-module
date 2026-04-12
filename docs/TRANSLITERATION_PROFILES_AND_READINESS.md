# Transliteration Profiles and Readiness

This build adds seeded transliteration profiles as first-class records.

What changed:
- transliteration profiles are now stored in SQLite
- transliteration responses can return the matching profile
- analysis output includes profile context
- system status includes transliteration profile counts and readiness summary
- low-resource language capability defaults are more conservative for Navajo, Cherokee, and Plains Cree

These profiles are broad hint layers, not a claim of strict scholarly romanization parity for every language.
