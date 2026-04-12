# Implementation Manifests and Phonology

This layer makes the package more honest about what is already implemented versus what still depends on external corpora or live backends.

## Added surfaces

- phonology_profiles: broad IPA, stress, and syllable hints
- backend_manifests: runtime expectations per provider
- corpus_manifests: installed vs external-required data sources
- implementation_matrix_reports: operator-facing summary of implemented, partial, and external-required surfaces
