from arc_lang.core.db import init_db
from arc_lang.services.seed_ingest import ingest_common_seed
from arc_lang.services.governance import set_language_capability
from arc_lang.services.orchestration import route_runtime_translation, route_runtime_speech
from arc_lang.core.models import CapabilityUpdateRequest, RuntimeTranslateRequest, RuntimeSpeechRequest


def setup_module(module):
    init_db()
    ingest_common_seed()


def test_runtime_translation_routes_local_seed_and_speech():
    set_language_capability(CapabilityUpdateRequest(language_id='lang:eng', capability_name='speech', maturity='experimental', confidence=0.82, provider='personaplex', notes='dry-run speech allowed'))
    result = route_runtime_translation(RuntimeTranslateRequest(text='hola', target_language_id='lang:eng', require_speech=True, speech_provider='personaplex'))
    assert result['ok'] is True
    assert result['translation']['translated_text'] == 'hello'
    assert result['routing']['selected_provider'] == 'local_seed'
    assert result['speech']['ok'] is True
    assert result['speech']['provider'] == 'personaplex'


def test_runtime_translation_blocks_when_no_translation_capability():
    result = route_runtime_translation(RuntimeTranslateRequest(text='unknown phrase', source_language_id='lang:eng', target_language_id='lang:chr'))
    assert result['ok'] is False
    assert result['error'] in {'translation_backend_not_implemented', 'translation_capability_unavailable', 'no_phrase_translation_found'}


def test_runtime_speech_capability_gate():
    blocked = route_runtime_speech(RuntimeSpeechRequest(text='hola', language_id='lang:spa'))
    assert blocked['ok'] is False
    assert blocked['error'] == 'speech_capability_unavailable'
