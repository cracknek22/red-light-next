import pytest

from redlight_next.core.errors import SerializationError
from redlight_next.core.serialization import dumps_json, loads_json, migrate_legacy_literal


def test_dumps_json_is_deterministic_json():
    assert dumps_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_loads_json_reads_valid_json():
    assert loads_json('{"items":[1,2]}') == {"items": [1, 2]}


def test_loads_json_rejects_python_literal():
    with pytest.raises(SerializationError):
        loads_json("{'not': 'json'}")


def test_legacy_literal_migration_does_not_execute_code():
    value = migrate_legacy_literal("{'old': ['cache', 1]}")
    assert value == {"old": ["cache", 1]}


def test_legacy_literal_rejects_code_execution_payload():
    with pytest.raises(SerializationError):
        migrate_legacy_literal("__import__('os').system('echo nope')")
