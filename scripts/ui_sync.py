#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULES_ROOT = ROOT / "app" / "features" / "modules"
_IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")

MUST_FIX_KEYS = (
    "unresolved_references",
    "new_definitions",
    "missing_assets",
    "locale_gaps",
    "duplicate_ids",
    "source_manifest_missing",
    "missing_name",
)
ADVISORY_KEYS = (
    "stale_entries",
    "conflicting_defaults",
    "roi_drift",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collect_ids(group: dict[str, Any]) -> set[str]:
    return {str(k) for k in group.keys()} if isinstance(group, dict) else set()


def _is_probable_ui_id(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if text.lower().endswith(_IMG_EXTS):
        return False
    if "/" in text or "\\" in text:
        return False
    if any(ch.isspace() for ch in text):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", text))


def _summarize_severity(summary: dict[str, int]) -> dict[str, int]:
    must_fix_count = sum(int(summary.get(k, 0)) for k in MUST_FIX_KEYS)
    advisory_count = sum(int(summary.get(k, 0)) for k in ADVISORY_KEYS)
    return {
        "must_fix_count": must_fix_count,
        "advisory_count": advisory_count,
    }


def _scan_code_refs(module_dir: Path) -> list[tuple[str, int, str]]:
    refs: list[tuple[str, int, str]] = []
    for py in module_dir.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # auto.click("start")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "click" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    if _is_probable_ui_id(first.value):
                        refs.append((str(py.relative_to(ROOT)).replace("\\", "/"), int(getattr(node, "lineno", 0)), first.value))
                    continue
                if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "U":
                    ref_id = None
                    for kw in first.keywords:
                        if kw.arg == "id" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            ref_id = kw.value.value
                            break
                    if ref_id is None and first.args and isinstance(first.args[0], ast.Constant) and isinstance(first.args[0].value, str):
                        ref_id = first.args[0].value
                    if ref_id:
                        refs.append((str(py.relative_to(ROOT)).replace("\\", "/"), int(getattr(node, "lineno", 0)), ref_id))
            # U("开始", id="start")
            if isinstance(node.func, ast.Name) and node.func.id == "U":
                ref_id = None
                for kw in node.keywords:
                    if kw.arg == "id" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        ref_id = kw.value.value
                        break
                if ref_id is None and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    ref_id = node.args[0].value
                if ref_id:
                    if _is_probable_ui_id(ref_id):
                        refs.append((str(py.relative_to(ROOT)).replace("\\", "/"), int(getattr(node, "lineno", 0)), ref_id))
    return refs


def _normalize_ui(module_id: str, ui_json: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    text = ui_json.get("text", {}) if isinstance(ui_json.get("text"), dict) else {}
    image = ui_json.get("image", {}) if isinstance(ui_json.get("image"), dict) else {}
    position = ui_json.get("position", {}) if isinstance(ui_json.get("position"), dict) else {}
    match = ui_json.get("match", {}) if isinstance(ui_json.get("match"), dict) else {}
    meta = ui_json.get("_meta", {}) if isinstance(ui_json.get("_meta"), dict) else {}

    report: dict[str, Any] = {
        "new_definitions": 0,
        "stale_entries": 0,
        "duplicate_ids": [],
        "conflicting_defaults": [],
        "missing_assets": [],
        "locale_gaps": [],
        "unresolved_references": [],
        "roi_drift": [],
        "missing_name": False,
    }
    name_value = ui_json.get("name")
    if not isinstance(name_value, str) or not name_value.strip():
        report["missing_name"] = True

    text_ids = _collect_ids(text)
    image_ids = _collect_ids(image)
    position_ids = _collect_ids(position)
    match_ids = _collect_ids(match) - {"_default"}

    duplicate = sorted((text_ids & image_ids))
    if duplicate:
        report["duplicate_ids"] = duplicate

    match_default = match.get("_default", {}) if isinstance(match.get("_default"), dict) else {}
    allowed_default_keys = {"threshold", "include", "need_ocr", "find_type"}
    for key in match_default.keys():
        if key not in allowed_default_keys:
            report["conflicting_defaults"].append(
                {"scope": "match._default", "key": str(key), "reason": "unknown_default_key"}
            )

    definitions: dict[str, Any] = {}
    all_ids = sorted(text_ids | image_ids | position_ids | match_ids)
    for ui_id in all_ids:
        text_node = text.get(ui_id, {}) if isinstance(text.get(ui_id), dict) else {}
        image_node = image.get(ui_id, {}) if isinstance(image.get(ui_id), dict) else {}
        pos_node = position.get(ui_id, {}) if isinstance(position.get(ui_id), dict) else {}
        match_node = match.get(ui_id, {}) if isinstance(match.get(ui_id), dict) else {}

        value = text_node.get("value")
        locale_text: dict[str, str] = {}
        if isinstance(value, str):
            locale_text["zh_CN"] = value
        elif isinstance(value, dict):
            for lang in ("zh_CN", "zh_HK", "en"):
                v = value.get(lang)
                if isinstance(v, str) and v.strip():
                    locale_text[lang] = v.strip()
        if ui_id in text_ids:
            for required in ("zh_CN", "en"):
                if required not in locale_text:
                    report["locale_gaps"].append({"id": ui_id, "missing_locale": required})

        image_path = image_node.get("path") if isinstance(image_node.get("path"), str) else None
        if image_path:
            if not (module_id and (MODULES_ROOT / module_id / "assets" / image_path).exists()):
                if not (ROOT / image_path).exists():
                    report["missing_assets"].append({"id": ui_id, "path": image_path})

        roi = pos_node.get("roi")
        if (not isinstance(roi, list)) and all(k in pos_node for k in ("x", "y", "w", "h")):
            roi = [pos_node.get("x"), pos_node.get("y"), pos_node.get("w"), pos_node.get("h")]
        if isinstance(roi, list) and len(roi) == 4:
            try:
                roi_f = [float(v) for v in roi]
                if any(v < 0 or v > 1 for v in roi_f):
                    report["roi_drift"].append({"id": ui_id, "roi": roi_f, "reason": "out_of_range"})
            except Exception:
                report["roi_drift"].append({"id": ui_id, "roi": roi, "reason": "invalid_number"})

        merged_match: dict[str, Any] = {}
        merged_match.update(match_default)
        merged_match.update(match_node)
        for key in allowed_default_keys:
            if key in match_default and key in match_node and match_default.get(key) != match_node.get(key):
                report["conflicting_defaults"].append(
                    {
                        "scope": ui_id,
                        "key": key,
                        "default": match_default.get(key),
                        "override": match_node.get(key),
                        "reason": "id_override_differs_from_default",
                    }
                )

        normalized_position = {}
        if isinstance(roi, list) and len(roi) == 4:
            normalized_position["roi"] = roi
            normalized_position["x"] = roi[0]
            normalized_position["y"] = roi[1]
            normalized_position["w"] = roi[2]
            normalized_position["h"] = roi[3]
        for k in ("x", "y", "w", "h", "anchor", "base_resolution"):
            if k in pos_node:
                normalized_position[k] = pos_node[k]

        definitions[ui_id] = {
            "id": ui_id,
            "text": locale_text,
            "aliases": text_node.get("aliases", []) if isinstance(text_node.get("aliases"), list) else [],
            "image": image_path,
            "position": normalized_position,
            "match": merged_match,
        }

    normalized = {
        "_meta": {
            "module_id": module_id,
            "schema_version": 1,
            "generated_by": "scripts/ui_sync.py",
            "source_meta": meta,
            "overlay_precedence": [
                "reference_override",
                "group.match[id]",
                "group.match._default",
                "definition_defaults",
            ],
        },
        "name": name_value if isinstance(name_value, str) and name_value.strip() else module_id,
        "definitions": definitions,
    }
    return normalized, report


def _generated_to_source_schema(generated: dict[str, Any]) -> dict[str, Any]:
    defs = generated.get("definitions", {}) if isinstance(generated.get("definitions"), dict) else {}
    text: dict[str, Any] = {}
    image: dict[str, Any] = {}
    position: dict[str, Any] = {}
    match: dict[str, Any] = {"_default": {}}

    for ui_id, node in defs.items():
        if not isinstance(node, dict):
            continue
        text_map = node.get("text", {}) if isinstance(node.get("text"), dict) else {}
        if text_map:
            text[str(ui_id)] = {
                "value": {k: v for k, v in text_map.items() if isinstance(k, str) and isinstance(v, str)},
                "aliases": node.get("aliases", []) if isinstance(node.get("aliases"), list) else [],
            }
        image_path = node.get("image")
        if isinstance(image_path, str) and image_path.strip():
            image[str(ui_id)] = {"path": image_path.strip()}
        pos = node.get("position", {}) if isinstance(node.get("position"), dict) else {}
        roi = pos.get("roi")
        pos_out: dict[str, Any] = {}
        if isinstance(roi, list) and len(roi) == 4:
            pos_out["roi"] = roi
        for k in ("x", "y", "w", "h", "anchor", "base_resolution"):
            if k in pos:
                pos_out[k] = pos[k]
        if pos_out:
            position[str(ui_id)] = pos_out
        m = node.get("match", {}) if isinstance(node.get("match"), dict) else {}
        if m:
            match[str(ui_id)] = {
                k: v for k, v in m.items() if k in {"threshold", "include", "need_ocr", "find_type"}
            }

    return {
        "name": generated.get("name") if isinstance(generated.get("name"), str) and generated.get("name").strip() else "",
        "_meta": {"schema_version": 1, "managed_by": "scripts/ui_sync.py"},
        "text": text,
        "image": image,
        "position": position,
        "match": match,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync and govern module UI resource manifests")
    parser.add_argument("--scan", action="store_true", help="Scan code references and manifests without writing")
    parser.add_argument("--write", action="store_true", help="Generate assets/ui.generated.json from assets/ui.json")
    parser.add_argument("--audit", action="store_true", help="Produce governance report only")
    parser.add_argument("--fail-on-issues", action="store_true", help="Return non-zero when governance issues are found")
    parser.add_argument("--fix", action="store_true", help="Apply safe automatic fixes (bootstrap missing source manifest)")
    parser.add_argument("--check", action="store_true", help="Compatibility alias of --audit")
    parser.add_argument(
        "--bootstrap-source",
        action="store_true",
        help="Create assets/ui.json from existing assets/ui.generated.json when source ui.json is missing",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {"modules": {}, "summary": defaultdict(int)}
    mode_scan = args.scan
    mode_audit = args.audit or args.check
    mode_fix = args.fix or args.bootstrap_source
    mode_write = args.write or args.fix or (not mode_scan and not mode_audit and not mode_fix)

    for module_dir in sorted(MODULES_ROOT.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("__"):
            continue
        module_id = module_dir.name
        ui_path = module_dir / "assets" / "ui.json"
        gen_path = module_dir / "assets" / "ui.generated.json"
        raw = _load_json(ui_path)
        generated_existing = _load_json(gen_path)
        if not raw and generated_existing:
            # Non-destructive baseline: do not lose existing generated definitions
            raw = _generated_to_source_schema(generated_existing)
            if mode_fix and not ui_path.exists():
                _save_json(ui_path, raw)
        if mode_fix and isinstance(raw, dict):
            if not isinstance(raw.get("name"), str) or not raw.get("name", "").strip():
                raw["name"] = module_id
                _save_json(ui_path, raw)
                raw = _load_json(ui_path)
        normalized, module_report = _normalize_ui(module_id, raw)

        refs = _scan_code_refs(module_dir)
        known_ids = set(normalized.get("definitions", {}).keys())
        ref_ids = {rid for _, _, rid in refs}
        unresolved_ids = sorted(ref_ids - known_ids)
        stale = sorted(known_ids - ref_ids)
        unresolved_details = [
            {"id": ref_id, "refs": [{"file": file, "line": line} for file, line, rid in refs if rid == ref_id]}
            for ref_id in unresolved_ids
        ]
        module_report["unresolved_references"] = unresolved_details
        module_report["stale_entries"] = len(stale)
        module_report["new_definitions"] = len(unresolved_ids)
        module_report["ref_count"] = len(ref_ids)
        module_report["def_count"] = len(known_ids)
        module_report["source_manifest_missing"] = not ui_path.exists()

        if mode_write:
            _save_json(gen_path, normalized)

        report["modules"][module_id] = module_report
        report["summary"]["modules"] += 1
        report["summary"]["unresolved_references"] += len(unresolved_ids)
        report["summary"]["stale_entries"] += len(stale)
        report["summary"]["new_definitions"] += len(unresolved_ids)
        report["summary"]["missing_assets"] += len(module_report["missing_assets"])
        report["summary"]["locale_gaps"] += len(module_report["locale_gaps"])
        report["summary"]["duplicate_ids"] += len(module_report["duplicate_ids"])
        report["summary"]["conflicting_defaults"] += len(module_report["conflicting_defaults"])
        report["summary"]["roi_drift"] += len(module_report["roi_drift"])
        report["summary"]["source_manifest_missing"] += 1 if module_report["source_manifest_missing"] else 0
        report["summary"]["missing_name"] += 1 if module_report.get("missing_name") else 0

    out_path = ROOT / "runtime" / "ui_sync_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_dict = dict(report["summary"])
    severity = _summarize_severity(summary_dict)
    _save_json(out_path, {"modules": report["modules"], "summary": summary_dict, "severity": severity})

    mode_name = "scan" if mode_scan else "audit" if mode_audit else "fix" if mode_fix else "write"
    print(f"mode={mode_name}")
    print(f"report={out_path}")
    print(f"modules={report['summary']['modules']}")
    print(f"unresolved_references={report['summary']['unresolved_references']}")
    print(f"stale_entries={report['summary']['stale_entries']}")
    print(f"new_definitions={report['summary']['new_definitions']}")
    print(f"missing_assets={report['summary']['missing_assets']}")
    print(f"locale_gaps={report['summary']['locale_gaps']}")
    print(f"duplicate_ids={report['summary']['duplicate_ids']}")
    print(f"conflicting_defaults={report['summary']['conflicting_defaults']}")
    print(f"roi_drift={report['summary']['roi_drift']}")
    print(f"source_manifest_missing={report['summary']['source_manifest_missing']}")
    print(f"missing_name={report['summary']['missing_name']}")
    print(f"must_fix_count={severity['must_fix_count']}")
    print(f"advisory_count={severity['advisory_count']}")

    if args.fail_on_issues:
        if severity["must_fix_count"] > 0:
            print(f"issue_count={severity['must_fix_count']}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
