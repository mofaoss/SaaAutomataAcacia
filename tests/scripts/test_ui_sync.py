from __future__ import annotations

from scripts.ui_sync import _generated_to_source_schema, _normalize_ui


def test_generated_to_source_schema_roundtrip_fields():
    generated = {
        "_meta": {"schema_version": 1},
        "definitions": {
            "start": {
                "text": {"zh_CN": "开始", "en": "Start"},
                "aliases": ["启动"],
                "image": "start.png",
                "position": {"roi": [0.1, 0.2, 0.3, 0.4]},
                "match": {"threshold": 0.8, "find_type": "image", "include": True, "need_ocr": False},
            }
        },
    }
    source = _generated_to_source_schema(generated)
    assert source["text"]["start"]["value"]["zh_CN"] == "开始"
    assert source["image"]["start"]["path"] == "start.png"
    assert source["position"]["start"]["roi"] == [0.1, 0.2, 0.3, 0.4]
    assert source["match"]["start"]["threshold"] == 0.8


def test_normalize_ui_reports_conflicting_defaults_and_locale_gap():
    ui_json = {
        "text": {"start": {"value": {"zh_CN": "开始"}}},
        "match": {
            "_default": {"threshold": 0.5, "bad_key": 1},
            "start": {"threshold": 0.9},
        },
    }
    _, report = _normalize_ui("demo_module", ui_json)
    assert any(item["reason"] == "unknown_default_key" for item in report["conflicting_defaults"])
    assert any(item["reason"] == "id_override_differs_from_default" for item in report["conflicting_defaults"])
    assert any(item["missing_locale"] == "en" for item in report["locale_gaps"])

