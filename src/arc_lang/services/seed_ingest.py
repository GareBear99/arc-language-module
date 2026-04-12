from __future__ import annotations
import json
import uuid
from pathlib import Path
from arc_lang.core.db import connect
from arc_lang.core.config import SEED_PATH, PHRASE_PATH, ETYMOLOGY_SEED_PATH, TRANSLITERATION_SEED_PATH, PHONOLOGY_SEED_PATH
from arc_lang.core.models import ScriptRecord, LanguageRecord, utcnow
from arc_lang.services.source_policy import seed_source_weights
from arc_lang.services.manifests import seed_manifests


def _upsert_provenance(conn, record_type: str, record_id: str, source_name: str, source_ref: str | None, confidence: float, notes: str, now: str) -> None:
    prov_id = f"prov_{record_type}_{record_id}_{source_name}".replace(":", "_").replace(" ", "_")
    conn.execute(
        """
        INSERT INTO provenance_records (provenance_id, record_type, record_id, source_name, source_ref, confidence, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(provenance_id) DO UPDATE SET source_ref=excluded.source_ref, confidence=excluded.confidence, notes=excluded.notes
        """,
        (prov_id, record_type, record_id, source_name, source_ref, confidence, notes, now),
    )


def _slug(text: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '_' for ch in text).strip('_')


def _ensure_lineage_node(conn, node_type: str, name: str, parent_node_id: str | None, now: str) -> str:
    node_id = f"{node_type}:{_slug(name)}"
    conn.execute(
        """
        INSERT INTO lineage_nodes (node_id, node_type, name, parent_node_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET name=excluded.name, parent_node_id=COALESCE(excluded.parent_node_id, lineage_nodes.parent_node_id), updated_at=excluded.updated_at
        """,
        (node_id, node_type, name, parent_node_id, now, now),
    )
    return node_id


def ingest_common_seed(seed_path: str | Path | None = None, phrase_path: str | Path | None = None, etymology_path: str | Path | None = None) -> dict:
    seed_path = Path(seed_path or SEED_PATH)
    phrase_path = Path(phrase_path or PHRASE_PATH)
    etymology_path = Path(etymology_path or ETYMOLOGY_SEED_PATH)
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    phrase_payload = json.loads(phrase_path.read_text(encoding="utf-8"))
    ety_payload = json.loads(etymology_path.read_text(encoding="utf-8"))
    pron_payload = json.loads((Path(__file__).resolve().parents[3] / 'config' / 'pronunciation_seed.json').read_text(encoding='utf-8'))
    phon_payload = json.loads(Path(PHONOLOGY_SEED_PATH).read_text(encoding='utf-8'))
    translit_payload = json.loads(Path(TRANSLITERATION_SEED_PATH).read_text(encoding='utf-8'))
    now = utcnow()
    seed_source_weights()
    seed_manifests()
    script_count = 0
    language_count = 0
    phrase_count = 0
    lexeme_count = 0
    etymology_count = 0
    pronunciation_count = 0
    transliteration_profile_count = 0
    phonology_count = 0
    with connect() as conn:

        seed_providers = [
            ("local_detect", "translation", 1, 1, "Local detection/runtime helper provider."),
            ("local_seed", "translation", 1, 1, "Local seeded phrase translation provider."),
            ("local_graph", "translation", 1, 1, "Local lineage/graph provider."),
            ("local_map", "translation", 1, 1, "Local transliteration mapping provider."),
            ("mirror_mock", "translation", 1, 1, "Local same-language mirror backend for runtime pipeline tests."),
            ("argos_local", "translation", 1, 1, "Optional local Argos Translate adapter when argostranslate is installed."),
            ("argos_bridge", "translation", 1, 0, "Boundary stub alias for future/live Argos bridge compatibility."),
            ("nllb_bridge", "translation", 1, 0, "Boundary stub for future NLLB translation adapter."),
            ("disabled", "speech", 1, 1, "Disabled speech sink for unsupported languages."),
            ("personaplex", "speech", 1, 0, "Optional NVIDIA PersonaPlex speech provider boundary."),
        ]
        for provider_name, provider_type, enabled, local_only, notes in seed_providers:
            conn.execute(
                """
                INSERT INTO provider_registry (provider_name, provider_type, enabled, local_only, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET provider_type=excluded.provider_type, enabled=excluded.enabled, local_only=excluded.local_only, notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (provider_name, provider_type, enabled, local_only, notes, now, now),
            )
        for script in payload.get("scripts", []):
            rec = ScriptRecord(**script)
            conn.execute(
                """
                INSERT OR REPLACE INTO scripts (script_id, name, unicode_ranges_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (rec.script_id, rec.name, json.dumps(rec.unicode_ranges, ensure_ascii=False), now),
            )
            _upsert_provenance(conn, "script", rec.script_id, "common_seed", f"config/common_languages_seed.json#{rec.script_id}", 0.95, "Seeded script record", now)
            script_count += 1

        for language in payload.get("languages", []):
            rec = LanguageRecord(**language)
            family_node_id = _ensure_lineage_node(conn, "family", rec.family, None, now) if rec.family else None
            branch_node_id = _ensure_lineage_node(conn, "branch", rec.branch, family_node_id, now) if rec.branch else None
            if family_node_id:
                _upsert_provenance(conn, 'lineage_node', family_node_id, rec.source_name, rec.source_ref or f"config/common_languages_seed.json#{rec.language_id}", rec.lineage_confidence, 'Seeded lineage family node.', now)
            if branch_node_id:
                _upsert_provenance(conn, 'lineage_node', branch_node_id, rec.source_name, rec.source_ref or f"config/common_languages_seed.json#{rec.language_id}", max(0.65, rec.lineage_confidence - 0.05), 'Seeded lineage branch node.', now)
            conn.execute(
                """
                INSERT INTO languages (
                    language_id, iso639_3, name, family, branch, parent_language_id,
                    family_node_id, branch_node_id, parent_node_id,
                    aliases_json, common_words_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(language_id) DO UPDATE SET
                    iso639_3=excluded.iso639_3,
                    name=excluded.name,
                    family=excluded.family,
                    branch=excluded.branch,
                    parent_language_id=excluded.parent_language_id,
                    family_node_id=excluded.family_node_id,
                    branch_node_id=excluded.branch_node_id,
                    parent_node_id=COALESCE(excluded.parent_node_id, languages.parent_node_id),
                    aliases_json=excluded.aliases_json,
                    common_words_json=excluded.common_words_json,
                    updated_at=excluded.updated_at
                """,
                (
                    rec.language_id, rec.iso639_3, rec.name, rec.family, rec.branch,
                    rec.parent_language_id, family_node_id, branch_node_id, None,
                    json.dumps(rec.aliases, ensure_ascii=False),
                    json.dumps(rec.common_words, ensure_ascii=False), now, now,
                ),
            )
            for script_id in rec.scripts:
                conn.execute(
                    "INSERT OR IGNORE INTO language_scripts (language_id, script_id) VALUES (?, ?)",
                    (rec.language_id, script_id),
                )
            if branch_node_id:
                edge_id = f"edge_{rec.language_id.replace(':','_')}_branch"
                conn.execute(
                    """
                    INSERT INTO lineage_edges (edge_id, src_id, dst_id, relation, confidence, disputed, source_ref, created_at)
                    VALUES (?, ?, ?, 'member_of_branch', ?, 0, ?, ?)
                    ON CONFLICT(edge_id) DO UPDATE SET dst_id=excluded.dst_id, confidence=excluded.confidence, source_ref=excluded.source_ref
                    """,
                    (edge_id, rec.language_id, branch_node_id, rec.lineage_confidence, rec.source_ref or rec.source_name, now),
                )
            elif family_node_id:
                edge_id = f"edge_{rec.language_id.replace(':','_')}_family"
                conn.execute(
                    """
                    INSERT INTO lineage_edges (edge_id, src_id, dst_id, relation, confidence, disputed, source_ref, created_at)
                    VALUES (?, ?, ?, 'member_of_family', ?, 0, ?, ?)
                    ON CONFLICT(edge_id) DO UPDATE SET dst_id=excluded.dst_id, confidence=excluded.confidence, source_ref=excluded.source_ref
                    """,
                    (edge_id, rec.language_id, family_node_id, rec.lineage_confidence, rec.source_ref or rec.source_name, now),
                )
            if rec.parent_language_id:
                edge_id = f"edge_{rec.language_id.replace(':','_')}_parent"
                conn.execute(
                    """
                    INSERT INTO lineage_edges (edge_id, src_id, dst_id, relation, confidence, disputed, source_ref, created_at)
                    VALUES (?, ?, ?, 'parent_of', ?, 0, ?, ?)
                    ON CONFLICT(edge_id) DO UPDATE SET dst_id=excluded.dst_id, confidence=excluded.confidence, source_ref=excluded.source_ref
                    """,
                    (edge_id, rec.language_id, rec.parent_language_id, max(0.65, rec.lineage_confidence - 0.1), rec.source_ref or rec.source_name, now),
                )
            _upsert_provenance(conn, "language", rec.language_id, rec.source_name, rec.source_ref or f"config/common_languages_seed.json#{rec.language_id}", rec.lineage_confidence, "Seeded language record", now)
            for alias_text in sorted(set([rec.name, *rec.aliases])):
                alias_type = 'endonym' if alias_text == rec.name else 'alias'
                alias_id = f"alias_{rec.language_id.replace(':','_')}_{alias_type}_{alias_text.lower().replace(' ','_')}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO language_aliases (alias_id, language_id, alias, normalized_form, alias_type, script_id, region_hint, source_name, source_ref, confidence, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (alias_id, rec.language_id, alias_text, alias_text.casefold().strip(), alias_type, rec.scripts[0] if rec.scripts else None, None, rec.source_name, rec.source_ref, rec.lineage_confidence, 'Seeded language alias.', now, now),
                )
            baseline_caps = [
                ("detection", "production", 0.93, "local_detect", "Seeded detection coverage."),
                ("lineage", "reviewed", rec.lineage_confidence, "local_graph", "Seeded lineage coverage."),
                ("translation", "seeded", 0.68, "local_seed", "Seeded phrase/lexeme coverage only."),
                ("speech", "none", 0.0, "disabled", "No seeded speech runtime by default."),
                ("pronunciation", "seeded", 0.66, "local_hint", "Seeded pronunciation hint profile available for some languages."),
                ("morphology", "seeded", 0.6, "local_analysis", "Seeded morphology/syntax assist available."),
            ]
            if any(s in {"Cyrl", "Cher", "Deva", "Arab", "Hebr"} for s in rec.scripts):
                baseline_caps.append(("transliteration", "seeded", 0.7, "local_map", "Basic transliteration mapping present."))
            else:
                baseline_caps.append(("transliteration", "experimental", 0.4, "local_map", "No guaranteed transliteration map yet."))
            low_resource_overrides = {
                'lang:nav': {
                    'translation': ("experimental", 0.42, "local_seed", "Low-resource language; seeded translation is sparse and experimental."),
                    'detection': ("reviewed", 0.72, "local_detect", "Lower-confidence low-resource detection coverage."),
                    'morphology': ("experimental", 0.45, "local_analysis", "Lower-resource morphology assist only."),
                },
                'lang:chr': {
                    'translation': ("experimental", 0.5, "local_seed", "Cherokee seeded coverage is limited and should be treated as experimental."),
                    'detection': ("reviewed", 0.76, "local_detect", "Cherokee detection is reviewed but not universal."),
                    'morphology': ("experimental", 0.5, "local_analysis", "Cherokee morphology assist remains limited."),
                },
                'lang:crk': {
                    'translation': ("experimental", 0.38, "local_seed", "Plains Cree coverage is sparse and experimental."),
                    'detection': ("reviewed", 0.68, "local_detect", "Plains Cree detection remains limited."),
                    'morphology': ("experimental", 0.42, "local_analysis", "Plains Cree morphology assist remains limited."),
                },
            }
            if rec.language_id in low_resource_overrides:
                for cap_name, override in low_resource_overrides[rec.language_id].items():
                    baseline_caps = [cap for cap in baseline_caps if not (cap[0] == cap_name and cap[3] == override[2])]
                    baseline_caps.append((cap_name, override[0], override[1], override[2], override[3]))
            for capability_name, maturity, cap_confidence, provider, notes in baseline_caps:
                capability_id = f"cap_{rec.language_id.replace(':','_')}_{capability_name}_{provider}"
                conn.execute(
                    """
                    INSERT INTO language_capabilities (capability_id, language_id, capability_name, maturity, confidence, provider, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(language_id, capability_name, provider) DO UPDATE SET maturity=excluded.maturity, confidence=excluded.confidence, notes=excluded.notes, updated_at=excluded.updated_at
                    """,
                    (capability_id, rec.language_id, capability_name, maturity, cap_confidence, provider, notes, now),
                )
            language_count += 1

        for phrase in phrase_payload.get("phrases", []):
            canonical_key = phrase["canonical_key"]
            for variant in phrase.get("variants", []):
                phrase_id = f"phr_{uuid.uuid5(uuid.NAMESPACE_URL, canonical_key + variant['language_id']).hex[:18]}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO phrase_translations (phrase_id, canonical_key, language_id, text_value, register, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (phrase_id, canonical_key, variant["language_id"], variant["text"], variant.get("register", "general"), now),
                )
                _upsert_provenance(conn, "phrase_translation", phrase_id, "common_phrase_seed", f"config/common_phrases_seed.json#{canonical_key}", 0.82, "Seeded common phrase translation", now)
                phrase_count += 1

        for lex in ety_payload.get('lexemes', []):
            conn.execute(
                """
                INSERT INTO lexemes (lexeme_id, language_id, lemma, gloss, canonical_meaning_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lexeme_id) DO UPDATE SET language_id=excluded.language_id, lemma=excluded.lemma, gloss=excluded.gloss, canonical_meaning_key=excluded.canonical_meaning_key, updated_at=excluded.updated_at
                """,
                (lex['lexeme_id'], lex['language_id'], lex['lemma'], lex.get('gloss'), lex.get('canonical_meaning_key'), now, now),
            )
            _upsert_provenance(conn, 'lexeme', lex['lexeme_id'], 'common_etymology_seed', f"config/common_etymologies_seed.json#{lex['lexeme_id']}", 0.75, 'Seeded lexeme record.', now)
            lexeme_count += 1
        for profile in pron_payload.get('profiles', []):
            profile_id = f"pron_{uuid.uuid5(uuid.NAMESPACE_URL, profile['language_id'] + ':' + profile['profile_kind']).hex[:18]}"
            conn.execute(
                """
                INSERT INTO pronunciation_profiles (profile_id, language_id, profile_kind, romanization_scheme, ipa_hint, examples_json, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET romanization_scheme=excluded.romanization_scheme, ipa_hint=excluded.ipa_hint, examples_json=excluded.examples_json, notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (profile_id, profile['language_id'], profile['profile_kind'], profile.get('romanization_scheme'), profile.get('ipa_hint'), json.dumps(profile.get('examples', {}), ensure_ascii=False), profile.get('notes', ''), now, now),
            )
            _upsert_provenance(conn, 'pronunciation_profile', profile_id, 'common_pronunciation_seed', f"config/pronunciation_seed.json#{profile['language_id']}", 0.7, 'Seeded pronunciation hint profile.', now)
            pronunciation_count += 1


        for profile in phon_payload.get('profiles', []):
            profile_id = f"phon_{uuid.uuid5(uuid.NAMESPACE_URL, profile['language_id'] + ':' + profile['notation_system']).hex[:18]}"
            conn.execute(
                """
                INSERT INTO phonology_profiles (profile_id, language_id, notation_system, broad_ipa, stress_policy, syllable_template, examples_json, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET broad_ipa=excluded.broad_ipa, stress_policy=excluded.stress_policy, syllable_template=excluded.syllable_template, examples_json=excluded.examples_json, notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (profile_id, profile['language_id'], profile['notation_system'], profile.get('broad_ipa'), profile.get('stress_policy'), profile.get('syllable_template'), json.dumps(profile.get('examples', {}), ensure_ascii=False), profile.get('notes', ''), now, now),
            )
            _upsert_provenance(conn, 'phonology_profile', profile_id, 'common_phonology_seed', f"config/phonology_seed.json#{profile['language_id']}", 0.62, 'Seeded phonology hint profile.', now)
            phonology_count += 1

        for profile in translit_payload.get('profiles', []):
            conn.execute(
                """
                INSERT INTO transliteration_profiles (profile_id, language_id, source_script, target_script, scheme_name, coverage, example_in, example_out, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET scheme_name=excluded.scheme_name, coverage=excluded.coverage, example_in=excluded.example_in, example_out=excluded.example_out, notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (profile['profile_id'], profile['language_id'], profile['source_script'], profile['target_script'], profile['scheme_name'], profile['coverage'], profile.get('example_in'), profile.get('example_out'), profile.get('notes', ''), now, now),
            )
            _upsert_provenance(conn, 'transliteration_profile', profile['profile_id'], 'common_transliteration_seed', f"config/transliteration_seed.json#{profile['profile_id']}", 0.68 if profile.get('coverage') == 'experimental' else 0.78, 'Seeded transliteration profile.', now)
            transliteration_profile_count += 1

        for edge in ety_payload.get('edges', []):
            etymology_id = f"ety_{uuid.uuid5(uuid.NAMESPACE_URL, edge['child_lexeme_id'] + '>' + edge['parent_lexeme_id']).hex[:18]}"
            conn.execute(
                """
                INSERT INTO etymology_edges (etymology_id, child_lexeme_id, parent_lexeme_id, relation, confidence, source_ref, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(etymology_id) DO UPDATE SET relation=excluded.relation, confidence=excluded.confidence, source_ref=excluded.source_ref
                """,
                (etymology_id, edge['child_lexeme_id'], edge['parent_lexeme_id'], edge['relation'], edge.get('confidence', 0.7), edge.get('source_ref'), now),
            )
            _upsert_provenance(conn, 'etymology_edge', etymology_id, 'common_etymology_seed', edge.get('source_ref'), edge.get('confidence', 0.7), 'Seeded etymology edge.', now)
            etymology_count += 1
        conn.commit()
    return {"ok": True, "scripts": script_count, "languages": language_count, "phrase_translations": phrase_count, "lexemes": lexeme_count, "etymology_edges": etymology_count, "pronunciation_profiles": pronunciation_count, "transliteration_profiles": transliteration_profile_count}
