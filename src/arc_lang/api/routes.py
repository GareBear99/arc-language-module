from __future__ import annotations
from fastapi import APIRouter, HTTPException
from arc_lang.core.db import init_db
from arc_lang.core.models import (
    PronunciationRequest,
    AnalysisRequest, TransliterationRequest, TransliterationProfileUpsertRequest, SemanticConceptUpsertRequest, ConceptLinkRequest, LanguageVariantUpsertRequest, ConflictReviewExportRequest, CoverageReportRequest,
    TranslationExplainRequest, SpeechRequest, TranslateExplainQuery, ImportRequest,
    ManualLineageRequest, LanguageSubmissionRequest, ReviewDecisionRequest, CapabilityUpdateRequest, RuntimeTranslateRequest, RuntimeSpeechRequest, ProviderRegistrationRequest, ProviderHealthRequest, TranslationInstallPlanRequest, PolicyUpdateRequest, EvidenceExportRequest, AliasUpsertRequest, RelationshipAssertionRequest, BatchImportRequest, BatchExportRequest, SourceWeightUpdateRequest, BackendActionRequest,
    AcquisitionJobRequest, StagedAssetRequest, ValidationReportRequest, IngestionWorkspaceExportRequest,
    PhonologyProfileUpsertRequest,
)
from arc_lang.services.seed_ingest import ingest_common_seed
from arc_lang.services.detection import detect_language
from arc_lang.services.lineage import get_lineage
from arc_lang.services.transliteration import transliterate, transliterate_request, list_transliteration_profiles, upsert_transliteration_profile
from arc_lang.services.translation_assertions import create_translation_assertion
from arc_lang.services.translate_explain import translate_explain
from arc_lang.services.speech_provider import get_provider
from arc_lang.services.importers import import_glottolog_csv, import_iso639_csv, import_cldr_json
from arc_lang.services.search import search_languages
from arc_lang.services.stats import get_graph_stats
from arc_lang.services.etymology import get_etymology
from arc_lang.services.manual_lineage import add_custom_lineage, list_custom_lineage
from arc_lang.services.onboarding import submit_language, list_language_submissions, approve_language_submission, export_language_submission_template, import_language_submission_json
from arc_lang.services.governance import record_review_decision, list_review_decisions, set_language_capability, list_language_capabilities, get_language_readiness
from arc_lang.services.arbitration import resolve_effective_lineage

router = APIRouter()


@router.get('/health')
def health() -> dict:
    return {'ok': True, 'service': 'arc_language_module', 'version': '0.24.0'}


@router.post('/init-db')
def init_database() -> dict:
    init_db()
    return {'ok': True}


@router.post('/seed/common')
def seed_common() -> dict:
    return ingest_common_seed()


@router.get('/detect')
def detect(text: str) -> dict:
    return detect_language(text).model_dump()


@router.get('/lineage/{language_id}')
def lineage(language_id: str) -> dict:
    result = get_lineage(language_id)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/transliterate')
def translit(text: str, source_script: str, target_script: str = 'Latn', language_id: str | None = None) -> dict:
    return transliterate(text=text, source_script=source_script, target_script=target_script, language_id=language_id)


@router.post('/transliterate')
def translit_post(req: TransliterationRequest) -> dict:
    return transliterate_request(req)


@router.post('/translation-assertions')
def translation_assertions(req: TranslationExplainRequest) -> dict:
    return create_translation_assertion(req)


@router.post('/translate-explain')
def translate_explain_route(req: TranslateExplainQuery) -> dict:
    result = translate_explain(req)
    if not result.get('ok') and result.get('error') == 'source_language_unknown':
        raise HTTPException(status_code=422, detail=result)
    return result


@router.post('/speak/{provider_name}')
def speak(provider_name: str, req: SpeechRequest) -> dict:
    provider = get_provider(provider_name)
    return provider.speak(req)


@router.post('/import/glottolog')
def import_glottolog(req: ImportRequest, dry_run: bool = False) -> dict:
    return import_glottolog_csv(req.path, dry_run=dry_run)


@router.post('/import/iso639_3')
def import_iso(req: ImportRequest, dry_run: bool = False) -> dict:
    return import_iso639_csv(req.path, dry_run=dry_run)


@router.post('/import/cldr')
def import_cldr(req: ImportRequest, dry_run: bool = False) -> dict:
    return import_cldr_json(req.path, dry_run=dry_run)


@router.get('/search/languages')
def search_language_route(q: str, limit: int = 20) -> dict:
    return search_languages(q, limit=limit)


@router.get('/etymology/{language_id}')
def etymology(language_id: str, lemma: str) -> dict:
    result = get_etymology(language_id, lemma)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/stats')
def stats() -> dict:
    return get_graph_stats()


@router.post('/lineage/custom')
def add_lineage_custom(req: ManualLineageRequest) -> dict:
    return add_custom_lineage(req)


@router.get('/lineage/custom')
def list_lineage_custom(src_id: str | None = None, dst_id: str | None = None, status: str | None = None) -> dict:
    return list_custom_lineage(src_id=src_id, dst_id=dst_id, status=status)


@router.post('/languages/submit')
def submit_language_route(req: LanguageSubmissionRequest) -> dict:
    return submit_language(req)


@router.get('/languages/submissions')
def list_language_submissions_route(status: str | None = None) -> dict:
    return list_language_submissions(status=status)


@router.post('/languages/submissions/{submission_id}/approve')
def approve_language_submission_route(submission_id: str, status: str = 'approved') -> dict:
    return approve_language_submission(submission_id, status=status)


@router.post('/languages/submissions/import-json')
def import_language_submission_route(req: ImportRequest) -> dict:
    return import_language_submission_json(req.path)


@router.post('/languages/submissions/export-template')
def export_language_submission_template_route(req: ImportRequest) -> dict:
    return export_language_submission_template(req.path)


@router.post('/governance/review')
def review_route(req: ReviewDecisionRequest) -> dict:
    return record_review_decision(req)


@router.get('/governance/reviews')
def review_list_route(target_type: str | None = None, target_id: str | None = None) -> dict:
    return list_review_decisions(target_type=target_type, target_id=target_id)


@router.post('/capabilities/set')
def capability_set_route(req: CapabilityUpdateRequest) -> dict:
    return set_language_capability(req)


@router.get('/capabilities')
def capability_list_route(language_id: str | None = None) -> dict:
    return list_language_capabilities(language_id=language_id)


@router.get('/capabilities/{language_id}/readiness')
def readiness_route(language_id: str) -> dict:
    result = get_language_readiness(language_id)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/lineage/{language_id}/effective')
def effective_lineage_route(language_id: str) -> dict:
    result = resolve_effective_lineage(language_id)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


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

@router.post('/runtime/translate')
def runtime_translate_route(req: RuntimeTranslateRequest) -> dict:
    result = route_runtime_translation(req)
    if not result.get('ok') and result.get('error') in {'source_language_unknown', 'translation_capability_unavailable', 'speech_capability_unavailable'}:
        raise HTTPException(status_code=422, detail=result)
    return result


@router.post('/runtime/speak')
def runtime_speak_route(req: RuntimeSpeechRequest) -> dict:
    result = route_runtime_speech(req)
    if not result.get('ok'):
        raise HTTPException(status_code=422, detail=result)
    return result


@router.post('/providers/register')
def provider_register_route(req: ProviderRegistrationRequest) -> dict:
    return register_provider(req.provider_name, req.provider_type, enabled=req.enabled, local_only=req.local_only, notes=req.notes)


@router.post('/providers/health')
def provider_health_route(req: ProviderHealthRequest) -> dict:
    return set_provider_health(req.provider_name, req.status, latency_ms=req.latency_ms, error_rate=req.error_rate, notes=req.notes)


@router.get('/providers')
def providers_route(provider_type: str | None = None) -> dict:
    return list_providers(provider_type=provider_type)


@router.get('/runtime/receipts')
def runtime_receipts_route(job_type: str | None = None, provider_name: str | None = None, limit: int = 50) -> dict:
    return list_job_receipts(job_type=job_type, provider_name=provider_name, limit=limit)


@router.get('/providers/translation-backends')
def translation_backends_route() -> dict:
    return list_builtin_translation_backends()


@router.get('/providers/diagnostics')
def provider_diagnostics_route(provider_name: str | None = None) -> dict:
    return get_provider_diagnostics(provider_name)


@router.get('/runtime/readiness/translation')
def translation_readiness_route(source_language_id: str, target_language_id: str, provider_name: str | None = None) -> dict:
    result = get_translation_pair_readiness(source_language_id, target_language_id, provider_name=provider_name)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/runtime/readiness/matrix')
def translation_readiness_matrix_route(target_language_id: str | None = None, provider_name: str | None = None, limit: int = 25) -> dict:
    return get_translation_readiness_matrix(target_language_id=target_language_id, provider_name=provider_name, limit=limit)


@router.get('/runtime/install-plan/translation')
def translation_install_plan_route(source_language_id: str, target_language_id: str, provider_name: str = 'argos_local') -> dict:
    result = build_translation_install_plan(source_language_id, target_language_id, provider_name=provider_name)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.post('/runtime/install-plan/translation/record')
def translation_install_plan_record_route(req: TranslationInstallPlanRequest) -> dict:
    result = record_translation_install_plan(req.source_language_id, req.target_language_id, provider_name=req.provider_name, notes=req.notes)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/runtime/install-plans')
def translation_install_plans_route(provider_name: str | None = None, source_language_id: str | None = None, target_language_id: str | None = None, limit: int = 50) -> dict:
    return list_translation_install_plans(provider_name=provider_name, source_language_id=source_language_id, target_language_id=target_language_id, limit=limit)


@router.get('/runtime/provider-actions')
def provider_actions_route(source_language_id: str, target_language_id: str, provider_name: str) -> dict:
    return build_provider_action_catalog(source_language_id, target_language_id, provider_name)


@router.post('/runtime/provider-actions/execute')
def provider_actions_execute_route(req: BackendActionRequest) -> dict:
    result = execute_provider_action(req)
    if not result.get('ok') and result.get('error') in {'provider_action_unknown', 'provider_action_mutation_blocked'}:
        raise HTTPException(status_code=422, detail=result)
    return result


@router.get('/runtime/provider-action-receipts')
def provider_action_receipts_route(provider_name: str | None = None, action_name: str | None = None, limit: int = 50) -> dict:
    return list_provider_action_receipts(provider_name=provider_name, action_name=action_name, limit=limit)


@router.get('/system/status')
def system_status_route() -> dict:
    return get_system_status()


@router.get('/policy')
def policy_route() -> dict:
    return get_policy_snapshot()


@router.post('/policy/set')
def policy_set_route(req: PolicyUpdateRequest) -> dict:
    return set_operator_policy(req.policy_key, req.policy_value, notes=req.notes)


@router.post('/evidence/export')
def evidence_export_route(req: EvidenceExportRequest) -> dict:
    return export_evidence_bundle(req.output_path, language_ids=req.language_ids, include_receipts=req.include_receipts, include_runtime=req.include_runtime, include_graph=req.include_graph)


@router.get('/transliteration/profiles')
def transliteration_profiles_route(language_id: str | None = None) -> dict:
    return list_transliteration_profiles(language_id=language_id)


@router.post('/transliteration/profiles/upsert')
def transliteration_profile_upsert_route(req: TransliterationProfileUpsertRequest) -> dict:
    return upsert_transliteration_profile(req.language_id, req.source_script, req.target_script, req.scheme_name, req.coverage, example_in=req.example_in, example_out=req.example_out, notes=req.notes)


@router.post('/pronounce')
def pronounce_route(req: PronunciationRequest) -> dict:
    result = pronunciation_guide(req)
    if not result.get('ok'):
        raise HTTPException(status_code=422, detail=result)
    return result


@router.get('/pronunciation/profiles')
def pronunciation_profiles_route(language_id: str | None = None) -> dict:
    return list_pronunciation_profiles(language_id=language_id)


@router.post('/analyze')
def analyze_route(req: AnalysisRequest) -> dict:
    result = analyze_text(req)
    if not result.get('ok'):
        raise HTTPException(status_code=422, detail=result)
    return result

from arc_lang.services.aliases import upsert_language_alias, list_language_aliases
from arc_lang.services.relationships import add_relationship_assertion, list_relationship_assertions
from arc_lang.services.batch_io import batch_import, batch_export, list_batch_runs
from arc_lang.services.source_policy import set_source_weight, list_source_weights


@router.post('/languages/aliases/upsert')
def alias_upsert_route(req: AliasUpsertRequest) -> dict:
    return upsert_language_alias(req)


@router.get('/languages/aliases')
def alias_list_route(language_id: str | None = None, q: str | None = None) -> dict:
    return list_language_aliases(language_id=language_id, q=q)


@router.post('/relationships/assert')
def relationship_assert_route(req: RelationshipAssertionRequest) -> dict:
    return add_relationship_assertion(req)


@router.get('/relationships')
def relationship_list_route(lexeme_id: str | None = None, relation: str | None = None) -> dict:
    return list_relationship_assertions(lexeme_id=lexeme_id, relation=relation)


@router.post('/batch/import')
def batch_import_route(req: BatchImportRequest) -> dict:
    return batch_import(req)


@router.post('/batch/export')
def batch_export_route(req: BatchExportRequest) -> dict:
    return batch_export(req)


@router.get('/batch/runs')
def batch_runs_route(mode: str | None = None, object_type: str | None = None) -> dict:
    return list_batch_runs(mode=mode, object_type=object_type)


@router.post('/sources/weights/set')
def source_weight_set_route(req: SourceWeightUpdateRequest) -> dict:
    return set_source_weight(req)


@router.get('/sources/weights')
def source_weight_list_route() -> dict:
    return list_source_weights()

from arc_lang.services.concepts import upsert_semantic_concept, link_concept, list_semantic_concepts, get_concept_bundle
from arc_lang.services.variants import upsert_language_variant, list_language_variants
from arc_lang.services.conflict_review import export_conflict_review_bundle, list_conflict_review_exports
from arc_lang.services.coverage import build_coverage_report, list_coverage_reports
from arc_lang.services.phonology import upsert_phonology_profile, list_phonology_profiles, phonology_hint
from arc_lang.services.manifests import list_backend_manifests, list_corpus_manifests
from arc_lang.services.implementation_matrix import build_implementation_matrix, list_implementation_matrix_reports

@router.post('/concepts/upsert')
def concepts_upsert_route(req: SemanticConceptUpsertRequest) -> dict:
    return upsert_semantic_concept(req)


@router.post('/concepts/link')
def concepts_link_route(req: ConceptLinkRequest) -> dict:
    return link_concept(req)


@router.get('/concepts')
def concepts_list_route(domain: str | None = None, q: str | None = None) -> dict:
    return list_semantic_concepts(domain=domain, q=q)


@router.get('/concepts/{concept_id}')
def concepts_bundle_route(concept_id: str) -> dict:
    result = get_concept_bundle(concept_id)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.post('/languages/variants/upsert')
def variants_upsert_route(req: LanguageVariantUpsertRequest) -> dict:
    return upsert_language_variant(req)


@router.get('/languages/variants')
def variants_list_route(language_id: str | None = None, variant_type: str | None = None) -> dict:
    return list_language_variants(language_id=language_id, variant_type=variant_type)


@router.post('/conflicts/export')
def conflicts_export_route(req: ConflictReviewExportRequest) -> dict:
    return export_conflict_review_bundle(req)


@router.get('/conflicts/exports')
def conflicts_exports_list_route(limit: int = 20) -> dict:
    return list_conflict_review_exports(limit=limit)


@router.post('/coverage/report')
def coverage_report_route(req: CoverageReportRequest) -> dict:
    return build_coverage_report(req)


@router.get('/coverage/reports')
def coverage_reports_route(limit: int = 20) -> dict:
    return list_coverage_reports(limit=limit)


@router.get('/phonology/profiles')
def phonology_profiles_route(language_id: str | None = None) -> dict:
    return list_phonology_profiles(language_id=language_id)


@router.post('/phonology/profiles/upsert')
def phonology_upsert_route(req: PhonologyProfileUpsertRequest) -> dict:
    return upsert_phonology_profile(
        req.language_id, req.notation_system,
        broad_ipa=req.broad_ipa,
        stress_policy=req.stress_policy,
        syllable_template=req.syllable_template,
        examples=req.examples or None,
        notes=req.notes,
    )


@router.get('/phonology/hint')
def phonology_hint_route(text: str, language_id: str) -> dict:
    result = phonology_hint(text, language_id)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/backend-manifests')
def backend_manifests_route(provider_name: str | None = None) -> dict:
    return list_backend_manifests(provider_name=provider_name)


@router.get('/corpus-manifests')
def corpus_manifests_route(corpus_kind: str | None = None) -> dict:
    return list_corpus_manifests(corpus_kind=corpus_kind)


@router.post('/implementation-matrix')
def implementation_matrix_route(output_path: str | None = None) -> dict:
    return build_implementation_matrix(output_path=output_path)


@router.get('/implementation-matrix/reports')
def implementation_matrix_reports_route(limit: int = 20) -> dict:
    return list_implementation_matrix_reports(limit=limit)

from arc_lang.services.acquisition_workspace import plan_acquisition_job, record_staged_asset, validate_staged_asset, list_acquisition_jobs, list_validation_reports, export_ingestion_workspace


@router.post('/acquisition/jobs')
def acquisition_job_route(req: AcquisitionJobRequest) -> dict:
    result = plan_acquisition_job(req)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/acquisition/jobs')
def acquisition_jobs_route(corpus_name: str | None = None) -> dict:
    return list_acquisition_jobs(corpus_name=corpus_name)


@router.post('/acquisition/assets')
def acquisition_asset_route(req: StagedAssetRequest) -> dict:
    result = record_staged_asset(req)
    if not result.get('ok'):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.post('/acquisition/validate')
def acquisition_validate_route(req: ValidationReportRequest) -> dict:
    result = validate_staged_asset(req)
    if not result.get('ok') and result.get('error') == 'file_not_found':
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get('/acquisition/validation-reports')
def acquisition_validation_reports_route(limit: int = 50) -> dict:
    return list_validation_reports(limit=limit)


@router.post('/acquisition/export-workspace')
def acquisition_export_workspace_route(req: IngestionWorkspaceExportRequest) -> dict:
    return export_ingestion_workspace(req)
