from __future__ import annotations
from arc_lang.core.db import connect


def get_graph_stats() -> dict:
    tables = {
        'languages': 'languages',
        'scripts': 'scripts',
        'lineage_nodes': 'lineage_nodes',
        'lineage_edges': 'lineage_edges',
        'phrase_translations': 'phrase_translations',
        'lexemes': 'lexemes',
        'etymology_edges': 'etymology_edges',
        'import_runs': 'import_runs',
        'review_decisions': 'review_decisions',
        'language_capabilities': 'language_capabilities',
        'providers': 'provider_registry',
        'job_receipts': 'job_receipts',
        'pronunciation_profiles': 'pronunciation_profiles',
        'phonology_profiles': 'phonology_profiles',
        'transliteration_profiles': 'transliteration_profiles',
        'semantic_concepts': 'semantic_concepts',
        'concept_links': 'concept_links',
        'language_variants': 'language_variants',
        'backend_manifests': 'backend_manifests',
        'corpus_manifests': 'corpus_manifests',
        'implementation_matrix_reports': 'implementation_matrix_reports'
    }
    counts = {}
    with connect() as conn:
        for key, table in tables.items():
            counts[key] = conn.execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']
    return {'ok': True, 'counts': counts}
