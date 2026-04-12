from __future__ import annotations
from arc_lang.core.db import connect


def search_languages(query: str, limit: int = 20) -> dict:
    q = f"%{query.strip().casefold()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT language_id, iso639_3, name, family, branch
            FROM languages
            WHERE lower(language_id) LIKE ? OR lower(name) LIKE ? OR lower(aliases_json) LIKE ? OR lower(COALESCE(family,'')) LIKE ? OR lower(COALESCE(branch,'')) LIKE ?
            ORDER BY name ASC
            LIMIT ?
            """,
            (q, q, q, q, q, limit),
        ).fetchall()
    return {'ok': True, 'query': query, 'results': [dict(r) for r in rows]}
