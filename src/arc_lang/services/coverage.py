
from __future__ import annotations
import json, uuid
from pathlib import Path
from arc_lang.core.db import connect
from arc_lang.core.models import CoverageReportRequest, utcnow
from arc_lang.services.governance import get_language_readiness


def build_coverage_report(req: CoverageReportRequest) -> dict:
    with connect() as conn:
        if req.language_ids:
            q = f"SELECT * FROM languages WHERE language_id IN ({','.join('?' for _ in req.language_ids)}) ORDER BY language_id"
            langs = [dict(r) for r in conn.execute(q, req.language_ids).fetchall()]
        else:
            langs = [dict(r) for r in conn.execute("SELECT * FROM languages ORDER BY language_id").fetchall()]
        items = []
        for lang in langs:
            lid = lang['language_id']
            alias_count = conn.execute("SELECT COUNT(*) AS c FROM language_aliases WHERE language_id=?", (lid,)).fetchone()['c']
            variant_count = conn.execute("SELECT COUNT(*) AS c FROM language_variants WHERE language_id=?", (lid,)).fetchone()['c']
            script_count = conn.execute("SELECT COUNT(*) AS c FROM language_scripts WHERE language_id=?", (lid,)).fetchone()['c']
            pron_count = conn.execute("SELECT COUNT(*) AS c FROM pronunciation_profiles WHERE language_id=?", (lid,)).fetchone()['c']
            translit_count = conn.execute("SELECT COUNT(*) AS c FROM transliteration_profiles WHERE language_id=?", (lid,)).fetchone()['c']
            concept_count = conn.execute("SELECT COUNT(*) AS c FROM concept_links WHERE target_type='language' AND target_id=?", (lid,)).fetchone()['c']
            readiness = get_language_readiness(lid).get('items', []) if req.include_runtime else []
            items.append({
                'language_id': lid,
                'name': lang['name'],
                'iso639_3': lang['iso639_3'],
                'aliases': alias_count,
                'variants': variant_count,
                'scripts': script_count,
                'pronunciation_profiles': pron_count,
                'transliteration_profiles': translit_count,
                'semantic_concepts': concept_count,
                'runtime_capabilities': readiness,
            })
    summary = {
        'languages': len(items),
        'with_variants': sum(1 for x in items if x['variants'] > 0),
        'with_concepts': sum(1 for x in items if x['semantic_concepts'] > 0),
        'with_transliteration_profiles': sum(1 for x in items if x['transliteration_profiles'] > 0),
    }
    payload = {'ok': True, 'summary': summary, 'items': items}
    if req.output_path:
        Path(req.output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        report_id = f"coverage_{uuid.uuid4().hex[:10]}"
        with connect() as conn:
            conn.execute("INSERT INTO coverage_reports (report_id, output_path, language_ids_json, summary_json, created_at) VALUES (?, ?, ?, ?, ?)", (report_id, req.output_path, json.dumps(req.language_ids, ensure_ascii=False), json.dumps(summary, ensure_ascii=False), utcnow()))
            conn.commit()
        payload['report_id'] = report_id
        payload['output_path'] = req.output_path
    return payload


def list_coverage_reports(limit: int = 20) -> dict:
    with connect() as conn:
        items = [dict(r) for r in conn.execute("SELECT * FROM coverage_reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
    return {'ok': True, 'count': len(items), 'items': items}
