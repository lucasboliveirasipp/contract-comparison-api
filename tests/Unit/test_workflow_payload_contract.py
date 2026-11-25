"""Contract test: o payload que geramos deve ter o MESMO shape do exemplo real da
Gateway (gateway_ocr_payload.json, fornecido pelo Jack). Se divergir, este teste pega.
"""

import json
from pathlib import Path

from src.services.juridico_service import _build_workflow_payload

FIXTURE = Path(__file__).parent.parent / "fixtures" / "gateway_ocr_payload.json"


def _step_props(payload):
    return payload["input_collection"]["input_properties"][0]["workflow_step_properties"]


def _full_paths(payload):
    return {p["full_path"] for p in _step_props(payload)}


def test_real_ocr_payload_has_expected_skeleton():
    real = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "workflow_configuration_code" in real
    assert real["input_collection"]["input_properties"][0]["workflow_step_order"] == 0
    assert _full_paths(real) == {"files_id", "container", "input_text"}


def test_our_payload_matches_real_skeleton(monkeypatch):
    monkeypatch.setenv("WORKFLOW_CODE_VERSOES", "WF_VERSOES")
    real = json.loads(FIXTURE.read_text(encoding="utf-8"))

    ours = _build_workflow_payload(["id-1", "id-2"], "cont-123")

    # mesma estrutura aninhada
    assert set(ours.keys()) == set(real.keys())
    assert ours["input_collection"]["input_properties"][0]["workflow_step_order"] == 0
    # mesmo conjunto de full_paths que o workflow real de arquivos espera (inclui input_text)
    assert _full_paths(ours) == _full_paths(real)


def test_our_payload_carries_file_refs_and_empty_input_text(monkeypatch):
    monkeypatch.setenv("WORKFLOW_CODE_VERSOES", "WF_VERSOES")
    ours = _build_workflow_payload(["id-1", "id-2"], "cont-123")
    by_path = {p["full_path"]: p["actual_value"] for p in _step_props(ours)}

    assert by_path["files_id"] == ["id-1", "id-2"]
    assert by_path["container"] == "cont-123"
    assert by_path["input_text"] == ""
