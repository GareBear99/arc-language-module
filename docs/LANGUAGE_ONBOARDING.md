# Language Onboarding

This module now supports safe onboarding of new languages through staged submissions.

## Flow
1. Create a submission JSON template.
2. Fill language identity, scripts, aliases, common words, and lineage hints.
3. Import the submission.
4. Review it in `language_submissions`.
5. Approve it to promote it into canonical `languages`, `language_scripts`, and lineage nodes.
6. Add optional custom lineage assertions when lineage is partial or disputed.

## Why this exists
- New languages should be addable without raw SQL edits.
- Submissions should not overwrite source-backed canonical data by accident.
- Custom lineage should be preserved with status and provenance.
