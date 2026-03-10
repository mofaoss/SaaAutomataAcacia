from __future__ import annotations

import json
from pathlib import Path

from app.framework.ui_resources.context import ModuleContext
from app.framework.ui_resources.manifest import ManifestEngine
from app.framework.ui_resources.models import UIReference
from app.framework.ui_resources.resolver import UIResolver


def test_manifest_engine_parses_generated_definitions(tmp_path: Path):
    generated = {
        "_meta": {"schema_version": 1},
        "definitions": {
            "start": {
                "text": {"zh_CN": "开始", "en": "Start"},
                "aliases": ["启动"],
                "image": "start.png",
                "position": {"roi": [0.1, 0.2, 0.3, 0.4]},
                "match": {"threshold": 0.77, "find_type": "image", "include": True, "need_ocr": False},
            }
        },
    }
    manifest = tmp_path / "ui.generated.json"
    manifest.write_text(json.dumps(generated, ensure_ascii=False), encoding="utf-8")
    snapshot = ManifestEngine().load("demo", manifest, None)
    assert "start" in snapshot.definitions
    item = snapshot.definitions["start"]
    assert item.threshold == 0.77
    assert item.roi == (0.1, 0.2, 0.3, 0.4)
    assert item.text["zh_CN"] == "开始"


def test_ui_resolver_reference_text_override_has_highest_precedence(monkeypatch, tmp_path: Path):
    generated = {
        "definitions": {
            "start": {
                "text": {"zh_CN": "开始", "en": "Start"},
                "position": {"roi": [0.1, 0.2, 0.3, 0.4]},
                "match": {"threshold": 0.66, "find_type": "text", "include": True, "need_ocr": True},
            }
        }
    }
    manifest = tmp_path / "ui.generated.json"
    manifest.write_text(json.dumps(generated, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("app.framework.ui_resources.resolver.is_non_chinese_ui_language", lambda: False)
    monkeypatch.setattr("app.framework.ui_resources.resolver.is_traditional_ui_language", lambda: False)
    ctx = ModuleContext(
        module_id="demo",
        module_dir=tmp_path,
        assets_dir=tmp_path,
        ui_manifest_path=None,
        generated_manifest_path=manifest,
        callsite_file="test.py",
        callsite_line=1,
    )
    ref = UIReference(id="start", text="手动覆盖", threshold=0.9)
    resolved = UIResolver().resolve(ref, ctx)
    assert resolved.target == "手动覆盖"
    assert resolved.threshold == 0.9
    assert resolved.find_type == "text"

