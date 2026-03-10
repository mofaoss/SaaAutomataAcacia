#!/usr/bin/env python
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUPPORTED_LANGS = ["en", "zh_CN", "zh_TW"]


def _line_offsets(src: str) -> list[int]:
    offs = [0]
    for i, ch in enumerate(src):
        if ch == "\n":
            offs.append(i + 1)
    return offs


def _to_index(line_offsets: list[int], lineno: int, col: int) -> int:
    return line_offsets[lineno - 1] + col


def _owner_i18n_dir(path: Path) -> Path:
    parts = path.parts
    if "modules" in parts:
        idx = parts.index("modules")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "i18n"
    return ROOT / "app" / "framework" / "i18n"


def _load_json(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _make_key(owner: Path, en_text: str) -> str:
    digest = hashlib.sha1(en_text.encode("utf-8")).hexdigest()[:12]
    if "modules" in owner.parts:
        module_name = owner.parts[owner.parts.index("modules") + 1]
        return f"module.{module_name}.legacy.{digest}"
    return f"framework.legacy.{digest}"


def _ensure_tr_import(lines: list[str]) -> list[str]:
    has_tr = any("from app.framework.i18n import tr" in line for line in lines)
    if has_tr:
        return lines
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = i + 1
    lines.insert(insert_at, "from app.framework.i18n import tr")
    return lines


def _remove_ui_text_import(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        if "from app.framework.ui.shared.text import ui_text" in line:
            continue
        out.append(line)
    return out


def migrate_file(path: Path) -> tuple[bool, dict[Path, dict[str, dict[str, str]]]]:
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    line_offsets = _line_offsets(src)
    replacements: list[tuple[int, int, str]] = []
    owner_updates: dict[Path, dict[str, dict[str, str]]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "ui_text":
            continue
        if len(node.args) < 2:
            continue
        zh_node, en_node = node.args[0], node.args[1]
        zh_src = ast.get_source_segment(src, zh_node) or "''"
        en_src = ast.get_source_segment(src, en_node) or "''"

        zh_const = zh_node.value if isinstance(zh_node, ast.Constant) and isinstance(zh_node.value, str) else None
        en_const = en_node.value if isinstance(en_node, ast.Constant) and isinstance(en_node.value, str) else None
        if en_const is None:
            key_seed = f"{path.as_posix()}:{node.lineno}:{node.col_offset}"
            key = "framework.legacy." + hashlib.sha1(key_seed.encode("utf-8")).hexdigest()[:12]
        else:
            key = _make_key(_owner_i18n_dir(path), en_const)

        start = _to_index(line_offsets, node.lineno, node.col_offset)
        end = _to_index(line_offsets, node.end_lineno, node.end_col_offset)
        replacements.append((start, end, f'tr("{key}", fallback={en_src})'))

        owner = _owner_i18n_dir(path)
        owner_updates.setdefault(owner, {lang: {} for lang in SUPPORTED_LANGS})
        if en_const is not None:
            owner_updates[owner]["en"][key] = en_const
        if zh_const is not None:
            owner_updates[owner]["zh_CN"][key] = zh_const
            owner_updates[owner]["zh_TW"][key] = zh_const

    if not replacements and "ui_text" not in src:
        return False, {}

    replacements.sort(key=lambda item: item[0], reverse=True)
    new_src = src
    for start, end, replacement in replacements:
        new_src = new_src[:start] + replacement + new_src[end:]

    lines = new_src.splitlines()
    lines = _remove_ui_text_import(lines)
    if any("tr(" in line for line in lines):
        lines = _ensure_tr_import(lines)
    final_src = "\n".join(lines) + ("\n" if new_src.endswith("\n") else "")
    path.write_text(final_src, encoding="utf-8")
    return True, owner_updates


def merge_updates(all_updates: dict[Path, dict[str, dict[str, str]]]) -> None:
    for owner_dir, lang_map in all_updates.items():
        for lang, updates in lang_map.items():
            if not updates:
                continue
            path = owner_dir / f"{lang}.json"
            current = _load_json(path)
            current.update(updates)
            _save_json(path, current)


def main() -> int:
    files = list((ROOT / "app").rglob("*.py"))
    changed = 0
    merged: dict[Path, dict[str, dict[str, str]]] = {}

    for path in files:
        ok, updates = migrate_file(path)
        if ok:
            changed += 1
        for owner, lang_map in updates.items():
            target = merged.setdefault(owner, {lang: {} for lang in SUPPORTED_LANGS})
            for lang in SUPPORTED_LANGS:
                target[lang].update(lang_map.get(lang, {}))

    merge_updates(merged)
    print(f"files_changed={changed}")
    print(f"i18n_owners_updated={len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
