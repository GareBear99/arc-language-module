from __future__ import annotations
import argparse
import json
from arc_lang.core.db import init_db
from arc_lang.core.models import TranslateExplainQuery, ManualLineageRequest, LanguageSubmissionRequest, ReviewDecisionRequest, CapabilityUpdateRequest, RuntimeTranslateRequest, RuntimeSpeechRequest, BackendActionRequest, PronunciationRequest, AnalysisRequest, TransliterationRequest, AliasUpsertRequest, RelationshipAssertionRequest, BatchImportRequest, BatchExportRequest, SourceWeightUpdateRequest, SemanticConceptUpsertRequest, ConceptLinkRequest, LanguageVariantUpsertRequest, ConflictReviewExportRequest, CoverageReportRequest, AcquisitionJobRequest, StagedAssetRequest, ValidationReportRequest, IngestionWorkspaceExportRequest
from arc_lang.services.seed_ingest import ingest_common_seed
from arc_lang.services.detection import detect_language, detect_script
from arc_lang.services.lineage import get_lineage
from arc_lang.services.transliteration import transliterate, transliterate_request, list_transliteration_profiles, upsert_transliteration_profile
from arc_lang.services.translate_explain import translate_explain
from arc_lang.services.importers import import_glottolog_csv, import_iso639_csv, import_cldr_json
from arc_lang.services.search import search_languages
from arc_lang.services.stats import get_graph_stats
from arc_lang.services.etymology import get_etymology
from arc_lang.services.manual_lineage import add_custom_lineage, list_custom_lineage
from arc_lang.services.onboarding import submit_language, list_language_submissions, approve_language_submission, export_language_submission_template, import_language_submission_json
from arc_lang.services.governance import record_review_decision, list_review_decisions, set_language_capability, list_language_capabilities, get_language_readiness
from arc_lang.services.arbitration import resolve_effective_lineage
from arc_lang.services.orchestration import route_runtime_translation, route_runtime_speech
from arc_lang.services.provider_registry import register_provider, set_provider_health, list_providers
from arc_lang.services.runtime_receipts import list_job_receipts
from arc_lang.services.translation_backends import list_builtin_translation_backends
from arc_lang.services.backend_diagnostics import get_provider_diagnostics, get_translation_pair_readiness, get_translation_readiness_matrix
from arc_lang.services.package_lifecycle import build_translation_install_plan, record_translation_install_plan, list_translation_install_plans
from arc_lang.services.provider_actions import build_provider_action_catalog, execute_provider_action, list_provider_action_receipts
from arc_lang.services.policy import get_policy_snapshot, set_operator_policy
from arc_lang.services.system_status import get_system_status
from arc_lang.services.evidence_export import export_evidence_bundle
from arc_lang.services.pronunciation import pronunciation_guide, list_pronunciation_profiles
from arc_lang.services.linguistic_analysis import analyze_text
from arc_lang.services.aliases import upsert_language_alias, list_language_aliases
from arc_lang.services.relationships import add_relationship_assertion, list_relationship_assertions
from arc_lang.services.batch_io import batch_import, batch_export, list_batch_runs
from arc_lang.services.source_policy import set_source_weight, list_source_weights
from arc_lang.services.concepts import upsert_semantic_concept, link_concept, list_semantic_concepts, get_concept_bundle
from arc_lang.services.variants import upsert_language_variant, list_language_variants
from arc_lang.services.conflict_review import export_conflict_review_bundle, list_conflict_review_exports
from arc_lang.services.coverage import build_coverage_report, list_coverage_reports
from arc_lang.services.acquisition_workspace import plan_acquisition_job, record_staged_asset, validate_staged_asset, list_acquisition_jobs, list_validation_reports, export_ingestion_workspace


def _dump(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog='arc-lang')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init-db')
    sub.add_parser('seed-common-languages')
    sub.add_parser('stats')

    p = sub.add_parser('detect'); p.add_argument('text')
    p = sub.add_parser('detect-script'); p.add_argument('text')
    p = sub.add_parser('lineage'); p.add_argument('language_id')
    p = sub.add_parser('effective-lineage'); p.add_argument('language_id')
    p = sub.add_parser('etymology'); p.add_argument('language_id'); p.add_argument('lemma')
    p = sub.add_parser('search-languages'); p.add_argument('query'); p.add_argument('--limit', type=int, default=20)
    p = sub.add_parser('transliterate'); p.add_argument('text'); p.add_argument('source_script'); p.add_argument('target_script', nargs='?', default='Latn')
    p = sub.add_parser('translate-explain'); p.add_argument('text'); p.add_argument('target_language_id'); p.add_argument('--source-language-id')
    p = sub.add_parser('pronounce'); p.add_argument('text'); p.add_argument('--language-id'); p.add_argument('--target-script', default='Latn')
    p = sub.add_parser('analyze-text'); p.add_argument('text'); p.add_argument('--language-id'); p.add_argument('--no-pronunciation', action='store_true')
    p = sub.add_parser('list-pronunciation-profiles'); p.add_argument('--language-id')
    p = sub.add_parser('list-transliteration-profiles'); p.add_argument('--language-id')
    p = sub.add_parser('upsert-transliteration-profile'); p.add_argument('language_id'); p.add_argument('source_script'); p.add_argument('target_script'); p.add_argument('scheme_name'); p.add_argument('coverage'); p.add_argument('--example-in'); p.add_argument('--example-out'); p.add_argument('--notes', default='')
    p = sub.add_parser('import-glottolog-fixture'); p.add_argument('path')
    p = sub.add_parser('import-iso-fixture'); p.add_argument('path')
    p = sub.add_parser('import-cldr-fixture'); p.add_argument('path')
    p = sub.add_parser('add-custom-lineage')
    p.add_argument('src_id'); p.add_argument('dst_id'); p.add_argument('--relation', default='custom_member_of_family')
    p.add_argument('--confidence', type=float, default=0.7); p.add_argument('--disputed', action='store_true')
    p.add_argument('--source-name', default='user_custom'); p.add_argument('--source-ref'); p.add_argument('--notes', default=''); p.add_argument('--status', default='user_asserted')
    p = sub.add_parser('list-custom-lineage'); p.add_argument('--src-id'); p.add_argument('--dst-id'); p.add_argument('--status')
    p = sub.add_parser('submit-language-json'); p.add_argument('path')
    p = sub.add_parser('submit-language-inline')
    p.add_argument('language_id'); p.add_argument('name'); p.add_argument('--iso639-3'); p.add_argument('--family'); p.add_argument('--branch'); p.add_argument('--parent-language-id')
    p.add_argument('--aliases', nargs='*', default=[]); p.add_argument('--common-words', nargs='*', default=[]); p.add_argument('--scripts', nargs='*', default=[])
    p.add_argument('--source-name', default='user_submission'); p.add_argument('--source-ref'); p.add_argument('--confidence', type=float, default=0.7)
    p.add_argument('--notes', default=''); p.add_argument('--status', default='submitted')
    p = sub.add_parser('list-language-submissions'); p.add_argument('--status')
    p = sub.add_parser('approve-language-submission'); p.add_argument('submission_id'); p.add_argument('--status', default='approved')
    p = sub.add_parser('export-language-template'); p.add_argument('path')
    p = sub.add_parser('review-target')
    p.add_argument('target_type'); p.add_argument('target_id'); p.add_argument('decision')
    p.add_argument('--reviewer', default='system_local'); p.add_argument('--confidence', type=float, default=0.8); p.add_argument('--notes', default='')
    p = sub.add_parser('list-reviews'); p.add_argument('--target-type'); p.add_argument('--target-id')
    p = sub.add_parser('set-language-capability')
    p.add_argument('language_id'); p.add_argument('capability_name'); p.add_argument('maturity')
    p.add_argument('--confidence', type=float, default=0.75); p.add_argument('--provider', default='local'); p.add_argument('--notes', default='')
    p = sub.add_parser('list-language-capabilities'); p.add_argument('--language-id')
    p = sub.add_parser('language-readiness'); p.add_argument('language_id')
    p = sub.add_parser('runtime-translate'); p.add_argument('text'); p.add_argument('target_language_id'); p.add_argument('--source-language-id'); p.add_argument('--preferred-translation-provider'); p.add_argument('--require-speech', action='store_true'); p.add_argument('--speech-provider'); p.add_argument('--voice-hint'); p.add_argument('--live', action='store_true')
    p = sub.add_parser('runtime-speak'); p.add_argument('text'); p.add_argument('language_id'); p.add_argument('--provider'); p.add_argument('--voice-hint'); p.add_argument('--live', action='store_true')
    p = sub.add_parser('register-provider'); p.add_argument('provider_name'); p.add_argument('provider_type'); p.add_argument('--disabled', action='store_true'); p.add_argument('--local-only', action='store_true'); p.add_argument('--notes', default='')
    p = sub.add_parser('set-provider-health'); p.add_argument('provider_name'); p.add_argument('status'); p.add_argument('--latency-ms', type=int); p.add_argument('--error-rate', type=float); p.add_argument('--notes', default='')
    p = sub.add_parser('list-providers'); p.add_argument('--provider-type')
    p = sub.add_parser('list-runtime-receipts'); p.add_argument('--job-type'); p.add_argument('--provider-name'); p.add_argument('--limit', type=int, default=50)
    p = sub.add_parser('provider-diagnostics'); p.add_argument('provider_name', nargs='?')
    p = sub.add_parser('translation-readiness'); p.add_argument('source_language_id'); p.add_argument('target_language_id'); p.add_argument('--provider')
    p = sub.add_parser('translation-readiness-matrix'); p.add_argument('--target-language-id'); p.add_argument('--provider'); p.add_argument('--limit', type=int, default=25)
    sub.add_parser('list-translation-backends')
    p = sub.add_parser('translation-install-plan'); p.add_argument('source_language_id'); p.add_argument('target_language_id'); p.add_argument('--provider', default='argos_local')
    p = sub.add_parser('record-translation-install-plan'); p.add_argument('source_language_id'); p.add_argument('target_language_id'); p.add_argument('--provider', default='argos_local'); p.add_argument('--note', action='append', default=[])
    p = sub.add_parser('list-translation-install-plans'); p.add_argument('--provider'); p.add_argument('--source-language-id'); p.add_argument('--target-language-id'); p.add_argument('--limit', type=int, default=50)

    sub.add_parser('system-status')
    sub.add_parser('show-policy')
    p = sub.add_parser('set-policy'); p.add_argument('policy_key'); p.add_argument('policy_value'); p.add_argument('--notes', default='')
    p = sub.add_parser('export-evidence'); p.add_argument('output_path'); p.add_argument('--language-id', action='append', default=[]); p.add_argument('--no-receipts', action='store_true'); p.add_argument('--no-runtime', action='store_true'); p.add_argument('--no-graph', action='store_true')
    p = sub.add_parser('provider-action-catalog'); p.add_argument('source_language_id'); p.add_argument('target_language_id'); p.add_argument('--provider', required=True)
    p = sub.add_parser('execute-provider-action'); p.add_argument('source_language_id'); p.add_argument('target_language_id'); p.add_argument('--provider', required=True); p.add_argument('--action-name'); p.add_argument('--apply', action='store_true'); p.add_argument('--allow-mutation', action='store_true'); p.add_argument('--note', action='append', default=[])
    p = sub.add_parser('list-provider-action-receipts'); p.add_argument('--provider'); p.add_argument('--action-name'); p.add_argument('--limit', type=int, default=50)

    p = sub.add_parser('upsert-language-alias'); p.add_argument('language_id'); p.add_argument('alias'); p.add_argument('alias_type'); p.add_argument('--normalized-form'); p.add_argument('--script-id'); p.add_argument('--region-hint'); p.add_argument('--source-name', default='user_custom'); p.add_argument('--source-ref'); p.add_argument('--confidence', type=float, default=0.8); p.add_argument('--notes', default='')
    p = sub.add_parser('list-language-aliases'); p.add_argument('--language-id'); p.add_argument('--query')
    p = sub.add_parser('assert-relationship'); p.add_argument('src_lexeme_id'); p.add_argument('dst_lexeme_id'); p.add_argument('relation'); p.add_argument('--confidence', type=float, default=0.7); p.add_argument('--disputed', action='store_true'); p.add_argument('--source-name', default='user_custom'); p.add_argument('--source-ref'); p.add_argument('--notes', default='')
    p = sub.add_parser('list-relationships'); p.add_argument('--lexeme-id'); p.add_argument('--relation')
    p = sub.add_parser('batch-import'); p.add_argument('input_path'); p.add_argument('object_type'); p.add_argument('--apply', action='store_true')
    p = sub.add_parser('batch-export'); p.add_argument('output_path'); p.add_argument('object_type'); p.add_argument('--language-id', action='append', default=[]); p.add_argument('--no-provenance', action='store_true')
    p = sub.add_parser('list-batch-runs'); p.add_argument('--mode'); p.add_argument('--object-type')
    p = sub.add_parser('set-source-weight'); p.add_argument('source_name'); p.add_argument('authority_weight', type=float); p.add_argument('--notes', default='')
    sub.add_parser('list-source-weights')
    p = sub.add_parser('upsert-semantic-concept'); p.add_argument('canonical_label'); p.add_argument('--concept-id'); p.add_argument('--domain', default='general'); p.add_argument('--description', default=''); p.add_argument('--source-name', default='user_custom'); p.add_argument('--source-ref'); p.add_argument('--confidence', type=float, default=0.8)
    p = sub.add_parser('link-concept'); p.add_argument('concept_id'); p.add_argument('target_type'); p.add_argument('target_id'); p.add_argument('--relation', default='expresses'); p.add_argument('--confidence', type=float, default=0.8); p.add_argument('--notes', default='')
    p = sub.add_parser('list-concepts'); p.add_argument('--domain'); p.add_argument('--query')
    p = sub.add_parser('concept-bundle'); p.add_argument('concept_id')
    p = sub.add_parser('upsert-language-variant'); p.add_argument('language_id'); p.add_argument('variant_name'); p.add_argument('variant_type'); p.add_argument('--region-hint'); p.add_argument('--script-id'); p.add_argument('--status', default='documented'); p.add_argument('--mutual-intelligibility', type=float); p.add_argument('--notes', default='')
    p = sub.add_parser('list-language-variants'); p.add_argument('--language-id'); p.add_argument('--variant-type')
    p = sub.add_parser('export-conflict-review'); p.add_argument('output_path'); p.add_argument('--language-id', action='append', default=[]); p.add_argument('--include-unreviewed-only', action='store_true')
    p = sub.add_parser('list-conflict-exports'); p.add_argument('--limit', type=int, default=20)
    p = sub.add_parser('coverage-report'); p.add_argument('--output-path'); p.add_argument('--language-id', action='append', default=[]); p.add_argument('--no-runtime', action='store_true'); p.add_argument('--no-graph', action='store_true')
    p = sub.add_parser('list-coverage-reports'); p.add_argument('--limit', type=int, default=20)

    args = parser.parse_args()
    if args.cmd == 'init-db': init_db(); _dump({'ok': True}); return
    if args.cmd == 'seed-common-languages': _dump(ingest_common_seed()); return
    if args.cmd == 'stats': _dump(get_graph_stats()); return
    if args.cmd == 'detect': _dump(detect_language(args.text).model_dump()); return
    if args.cmd == 'detect-script': _dump({'ok': True, 'script': detect_script(args.text)}); return
    if args.cmd == 'lineage': _dump(get_lineage(args.language_id)); return
    if args.cmd == 'effective-lineage': _dump(resolve_effective_lineage(args.language_id)); return
    if args.cmd == 'etymology': _dump(get_etymology(args.language_id, args.lemma)); return
    if args.cmd == 'search-languages': _dump(search_languages(args.query, limit=args.limit)); return
    if args.cmd == 'transliterate': _dump(transliterate(args.text, args.source_script, args.target_script)); return
    if args.cmd == 'translate-explain': _dump(translate_explain(TranslateExplainQuery(text=args.text, target_language_id=args.target_language_id, source_language_id=args.source_language_id))); return
    if args.cmd == 'pronounce': _dump(pronunciation_guide(PronunciationRequest(text=args.text, language_id=args.language_id, target_script=args.target_script))); return
    if args.cmd == 'analyze-text': _dump(analyze_text(AnalysisRequest(text=args.text, language_id=args.language_id, include_pronunciation=not args.no_pronunciation))); return
    if args.cmd == 'list-pronunciation-profiles': _dump(list_pronunciation_profiles(language_id=args.language_id)); return
    if args.cmd == 'list-transliteration-profiles': _dump(list_transliteration_profiles(language_id=args.language_id)); return
    if args.cmd == 'upsert-transliteration-profile': _dump(upsert_transliteration_profile(args.language_id, args.source_script, args.target_script, args.scheme_name, args.coverage, example_in=args.example_in, example_out=args.example_out, notes=args.notes)); return
    if args.cmd == 'import-glottolog-fixture': _dump(import_glottolog_csv(args.path)); return
    if args.cmd == 'import-iso-fixture': _dump(import_iso639_csv(args.path)); return
    if args.cmd == 'import-cldr-fixture': _dump(import_cldr_json(args.path)); return
    if args.cmd == 'add-custom-lineage':
        _dump(add_custom_lineage(ManualLineageRequest(src_id=args.src_id, dst_id=args.dst_id, relation=args.relation, confidence=args.confidence, disputed=args.disputed, source_name=args.source_name, source_ref=args.source_ref, notes=args.notes, status=args.status)));
        return
    if args.cmd == 'list-custom-lineage': _dump(list_custom_lineage(src_id=args.src_id, dst_id=args.dst_id, status=args.status)); return
    if args.cmd == 'submit-language-json': _dump(import_language_submission_json(args.path)); return
    if args.cmd == 'submit-language-inline':
        _dump(submit_language(LanguageSubmissionRequest(language_id=args.language_id, name=args.name, iso639_3=args.iso639_3, family=args.family, branch=args.branch, parent_language_id=args.parent_language_id, aliases=args.aliases, common_words=args.common_words, scripts=args.scripts, source_name=args.source_name, source_ref=args.source_ref, confidence=args.confidence, notes=args.notes, status=args.status)));
        return
    if args.cmd == 'list-language-submissions': _dump(list_language_submissions(status=args.status)); return
    if args.cmd == 'approve-language-submission': _dump(approve_language_submission(args.submission_id, status=args.status)); return
    if args.cmd == 'export-language-template': _dump(export_language_submission_template(args.path)); return
    if args.cmd == 'review-target':
        _dump(record_review_decision(ReviewDecisionRequest(target_type=args.target_type, target_id=args.target_id, decision=args.decision, reviewer=args.reviewer, confidence=args.confidence, notes=args.notes)));
        return
    if args.cmd == 'list-reviews': _dump(list_review_decisions(target_type=args.target_type, target_id=args.target_id)); return
    if args.cmd == 'set-language-capability':
        _dump(set_language_capability(CapabilityUpdateRequest(language_id=args.language_id, capability_name=args.capability_name, maturity=args.maturity, confidence=args.confidence, provider=args.provider, notes=args.notes)));
        return
    if args.cmd == 'list-language-capabilities': _dump(list_language_capabilities(language_id=args.language_id)); return
    if args.cmd == 'language-readiness': _dump(get_language_readiness(args.language_id)); return
    if args.cmd == 'runtime-translate':
        _dump(route_runtime_translation(RuntimeTranslateRequest(text=args.text, target_language_id=args.target_language_id, source_language_id=args.source_language_id, preferred_translation_provider=args.preferred_translation_provider, require_speech=args.require_speech, speech_provider=args.speech_provider, voice_hint=args.voice_hint, dry_run=not args.live))); return
    if args.cmd == 'runtime-speak':
        _dump(route_runtime_speech(RuntimeSpeechRequest(text=args.text, language_id=args.language_id, provider=args.provider, voice_hint=args.voice_hint, dry_run=not args.live))); return
    if args.cmd == 'register-provider': _dump(register_provider(args.provider_name, args.provider_type, enabled=not args.disabled, local_only=args.local_only, notes=args.notes)); return
    if args.cmd == 'set-provider-health': _dump(set_provider_health(args.provider_name, args.status, latency_ms=args.latency_ms, error_rate=args.error_rate, notes=args.notes)); return
    if args.cmd == 'list-providers': _dump(list_providers(provider_type=args.provider_type)); return
    if args.cmd == 'list-runtime-receipts': _dump(list_job_receipts(job_type=args.job_type, provider_name=args.provider_name, limit=args.limit)); return
    if args.cmd == 'provider-diagnostics': _dump(get_provider_diagnostics(args.provider_name)); return
    if args.cmd == 'translation-readiness': _dump(get_translation_pair_readiness(args.source_language_id, args.target_language_id, provider_name=args.provider)); return
    if args.cmd == 'translation-readiness-matrix': _dump(get_translation_readiness_matrix(target_language_id=args.target_language_id, provider_name=args.provider, limit=args.limit)); return
    if args.cmd == 'list-translation-backends': _dump(list_builtin_translation_backends()); return
    if args.cmd == 'translation-install-plan': _dump(build_translation_install_plan(args.source_language_id, args.target_language_id, provider_name=args.provider)); return
    if args.cmd == 'record-translation-install-plan': _dump(record_translation_install_plan(args.source_language_id, args.target_language_id, provider_name=args.provider, notes=args.note)); return
    if args.cmd == 'list-translation-install-plans': _dump(list_translation_install_plans(provider_name=args.provider, source_language_id=args.source_language_id, target_language_id=args.target_language_id, limit=args.limit)); return

    if args.cmd == 'system-status': _dump(get_system_status()); return
    if args.cmd == 'show-policy': _dump(get_policy_snapshot()); return
    if args.cmd == 'set-policy': _dump(set_operator_policy(args.policy_key, args.policy_value, notes=args.notes)); return
    if args.cmd == 'export-evidence': _dump(export_evidence_bundle(args.output_path, language_ids=args.language_id, include_receipts=not args.no_receipts, include_runtime=not args.no_runtime, include_graph=not args.no_graph)); return
    if args.cmd == 'provider-action-catalog': _dump(build_provider_action_catalog(args.source_language_id, args.target_language_id, args.provider)); return
    if args.cmd == 'execute-provider-action': _dump(execute_provider_action(BackendActionRequest(provider_name=args.provider, source_language_id=args.source_language_id, target_language_id=args.target_language_id, action_name=args.action_name, dry_run=not args.apply, allow_mutation=args.allow_mutation, notes=args.note))); return
    if args.cmd == 'list-provider-action-receipts': _dump(list_provider_action_receipts(provider_name=args.provider, action_name=args.action_name, limit=args.limit)); return

    if args.cmd == 'upsert-language-alias': _dump(upsert_language_alias(AliasUpsertRequest(language_id=args.language_id, alias=args.alias, alias_type=args.alias_type, normalized_form=args.normalized_form, script_id=args.script_id, region_hint=args.region_hint, source_name=args.source_name, source_ref=args.source_ref, confidence=args.confidence, notes=args.notes))); return
    if args.cmd == 'list-language-aliases': _dump(list_language_aliases(language_id=args.language_id, q=args.query)); return
    if args.cmd == 'assert-relationship': _dump(add_relationship_assertion(RelationshipAssertionRequest(src_lexeme_id=args.src_lexeme_id, dst_lexeme_id=args.dst_lexeme_id, relation=args.relation, confidence=args.confidence, disputed=args.disputed, source_name=args.source_name, source_ref=args.source_ref, notes=args.notes))); return
    if args.cmd == 'list-relationships': _dump(list_relationship_assertions(lexeme_id=args.lexeme_id, relation=args.relation)); return
    if args.cmd == 'batch-import': _dump(batch_import(BatchImportRequest(input_path=args.input_path, object_type=args.object_type, dry_run=not args.apply))); return
    if args.cmd == 'batch-export': _dump(batch_export(BatchExportRequest(output_path=args.output_path, object_type=args.object_type, language_ids=args.language_id, include_provenance=not args.no_provenance))); return
    if args.cmd == 'list-batch-runs': _dump(list_batch_runs(mode=args.mode, object_type=args.object_type)); return
    if args.cmd == 'set-source-weight': _dump(set_source_weight(SourceWeightUpdateRequest(source_name=args.source_name, authority_weight=args.authority_weight, notes=args.notes))); return
    if args.cmd == 'list-source-weights': _dump(list_source_weights()); return
    if args.cmd == 'upsert-semantic-concept': _dump(upsert_semantic_concept(SemanticConceptUpsertRequest(concept_id=args.concept_id, canonical_label=args.canonical_label, domain=args.domain, description=args.description, source_name=args.source_name, source_ref=args.source_ref, confidence=args.confidence))); return
    if args.cmd == 'link-concept': _dump(link_concept(ConceptLinkRequest(concept_id=args.concept_id, target_type=args.target_type, target_id=args.target_id, relation=args.relation, confidence=args.confidence, notes=args.notes))); return
    if args.cmd == 'list-concepts': _dump(list_semantic_concepts(domain=args.domain, q=args.query)); return
    if args.cmd == 'concept-bundle': _dump(get_concept_bundle(args.concept_id)); return
    if args.cmd == 'upsert-language-variant': _dump(upsert_language_variant(LanguageVariantUpsertRequest(language_id=args.language_id, variant_name=args.variant_name, variant_type=args.variant_type, region_hint=args.region_hint, script_id=args.script_id, status=args.status, mutual_intelligibility=args.mutual_intelligibility, notes=args.notes))); return
    if args.cmd == 'list-language-variants': _dump(list_language_variants(language_id=args.language_id, variant_type=args.variant_type)); return
    if args.cmd == 'export-conflict-review': _dump(export_conflict_review_bundle(ConflictReviewExportRequest(output_path=args.output_path, language_ids=args.language_id, include_unreviewed_only=args.include_unreviewed_only))); return
    if args.cmd == 'list-conflict-exports': _dump(list_conflict_review_exports(limit=args.limit)); return
    if args.cmd == 'coverage-report': _dump(build_coverage_report(CoverageReportRequest, AcquisitionJobRequest, StagedAssetRequest, ValidationReportRequest, IngestionWorkspaceExportRequest(output_path=args.output_path, language_ids=args.language_id, include_runtime=not args.no_runtime, include_graph=not args.no_graph))); return
    if args.cmd == 'list-coverage-reports': _dump(list_coverage_reports(limit=args.limit)); return


if __name__ == '__main__':
    main()
