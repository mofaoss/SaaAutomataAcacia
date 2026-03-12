#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.framework.i18n.runtime import classify_source_language

TARGET_REFS = [
    "main",
    "feat/autopage-optimization",
    "backup_pre_refactor_final_20260311",
    "remotes/origin/feature/ui-decouple-qt",
]

_PH_NORM_RE = re.compile(r"\{[^{}]*\}")
_PH_TOKEN_RE = re.compile(r"\{([^{}]+)\}")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")


@dataclass
class Edit:
    start: int
    end: int
    replacement: str


def _norm_text(s: str) -> str:
    return " ".join(_PH_NORM_RE.sub("{}", s.strip().lower()).split())


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    cursor = 0
    for line in text.splitlines(keepends=True):
        cursor += len(line.encode("utf-8"))
        offsets.append(cursor)
    return offsets


def _to_offset(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[lineno - 1] + col


def _parse_placeholder_names(text: str) -> list[str]:
    names: list[str] = []
    for m in _PH_TOKEN_RE.finditer(text):
        inner = m.group(1)
        name = inner.split(":", 1)[0].split("!", 1)[0]
        if name not in names:
            names.append(name)
    return names


def _adapt_placeholder_names(zh_text: str, en_text: str) -> str | None:
    src_names = _parse_placeholder_names(zh_text)
    tgt_names = _parse_placeholder_names(en_text)
    if set(src_names) == set(tgt_names):
        return zh_text
    if len(src_names) != len(tgt_names):
        return None
    if not src_names:
        return zh_text
    mapping = {src: tgt for src, tgt in zip(src_names, tgt_names)}

    def repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        src_name = inner.split(":", 1)[0].split("!", 1)[0]
        suffix = inner[len(src_name):]
        return "{" + mapping.get(src_name, src_name) + suffix + "}"

    return _PH_TOKEN_RE.sub(repl, zh_text)


def _git_show_text(ref: str, rel_path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{rel_path}"], capture_output=True)
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except Exception:
        return None


def _list_ref_files(ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "app"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def _build_translation_maps() -> tuple[dict[str, str], dict[str, str]]:
    exact: dict[str, str] = {}
    normed: dict[str, str] = {}

    def is_valid_zh_source(text: str) -> bool:
        try:
            return classify_source_language(text) == "zh_CN"
        except Exception:
            return False

    for ref in TARGET_REFS:
        for rel_path in _list_ref_files(ref):
            if rel_path.endswith(".py"):
                raw = _git_show_text(ref, rel_path)
                if raw is None:
                    continue
                try:
                    tree = ast.parse(raw)
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call) or len(node.args) < 2:
                        continue
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    if func_name not in {"ui_text", "_ui_text", "_"}:
                        continue
                    a0, a1 = node.args[0], node.args[1]
                    if not (
                        isinstance(a0, ast.Constant)
                        and isinstance(a0.value, str)
                        and isinstance(a1, ast.Constant)
                        and isinstance(a1.value, str)
                    ):
                        continue
                    zh_text = a0.value.strip()
                    en_text = a1.value.strip()
                    if not zh_text or not en_text:
                        continue
                    if not _CJK_RE.search(zh_text) or not is_valid_zh_source(zh_text):
                        continue
                    exact.setdefault(en_text, zh_text)
                    normed.setdefault(_norm_text(en_text), zh_text)
            elif rel_path.endswith("/i18n/en.json"):
                zh_rel = rel_path.replace("/en.json", "/zh_CN.json")
                en_raw = _git_show_text(ref, rel_path)
                zh_raw = _git_show_text(ref, zh_rel)
                if en_raw is None or zh_raw is None:
                    continue
                try:
                    en_map = json.loads(en_raw)
                    zh_map = json.loads(zh_raw)
                except Exception:
                    continue
                if not isinstance(en_map, dict) or not isinstance(zh_map, dict):
                    continue
                for k, en_text in en_map.items():
                    zh_text = zh_map.get(k)
                    if not isinstance(en_text, str) or not isinstance(zh_text, str):
                        continue
                    zh_text = zh_text.strip()
                    if not zh_text or not _CJK_RE.search(zh_text) or not is_valid_zh_source(zh_text):
                        continue
                    exact.setdefault(en_text, zh_text)
                    normed.setdefault(_norm_text(en_text), zh_text)

    # Also use current catalog pairs as translation memory.
    for en_path in APP_ROOT.rglob("i18n/en.json"):
        zh_path = en_path.with_name("zh_CN.json")
        if not zh_path.exists():
            continue
        try:
            en_map = json.loads(en_path.read_text(encoding="utf-8"))
            zh_map = json.loads(zh_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(en_map, dict) or not isinstance(zh_map, dict):
            continue
        for k, en_text in en_map.items():
            zh_text = zh_map.get(k)
            if not isinstance(en_text, str) or not isinstance(zh_text, str):
                continue
            zh_text = zh_text.strip()
            if not zh_text or not _CJK_RE.search(zh_text) or not is_valid_zh_source(zh_text):
                continue
            exact.setdefault(en_text, zh_text)
            normed.setdefault(_norm_text(en_text), zh_text)

    return exact, normed


def _collect_edits_for_file(path: Path, exact_map: dict[str, str], norm_map: dict[str, str]) -> tuple[list[Edit], int]:
    source = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return [], 0

    offsets = _line_offsets(source)
    edits: list[Edit] = []
    scanned = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "_"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        en_text = first.value
        scanned += 1
        zh_text = exact_map.get(en_text)
        if zh_text is None:
            zh_text = norm_map.get(_norm_text(en_text))
        if zh_text is None:
            continue
        adapted = _adapt_placeholder_names(zh_text, en_text)
        if adapted is None:
            continue
        if adapted == en_text:
            continue
        if not hasattr(first, "end_lineno") or not hasattr(first, "end_col_offset"):
            continue
        replacement = ast.unparse(ast.Constant(value=adapted))
        start = _to_offset(offsets, int(first.lineno), int(first.col_offset))
        end = _to_offset(offsets, int(first.end_lineno), int(first.end_col_offset))
        edits.append(Edit(start=start, end=end, replacement=replacement))

    edits.sort(key=lambda e: e.start, reverse=True)
    return edits, scanned


def _apply_edits(source: str, edits: list[Edit]) -> str:
    raw = source.encode("utf-8")
    for edit in edits:
        raw = raw[: edit.start] + edit.replacement.encode("utf-8") + raw[edit.end :]
    return raw.decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace _('English') with historical _('中文') by translation memory.")
    parser.add_argument("--write", action="store_true", help="Write changes to disk.")
    parser.add_argument("paths", nargs="*", default=["app"], help="Files or directories to scan.")
    args = parser.parse_args()

    exact_map, norm_map = _build_translation_maps()

    targets: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if not path.is_absolute():
            path = (ROOT / p).resolve()
        if path.is_file() and path.suffix == ".py":
            targets.append(path)
        elif path.is_dir():
            targets.extend(path.rglob("*.py"))
    targets = sorted(set(targets))

    files_changed = 0
    calls_changed = 0
    calls_scanned = 0

    for path in targets:
        source = path.read_text(encoding="utf-8-sig")
        edits, scanned = _collect_edits_for_file(path, exact_map, norm_map)
        calls_scanned += scanned
        if not edits:
            continue
        updated = _apply_edits(source, edits)
        if updated == source:
            continue
        ast.parse(updated, filename=str(path))
        if args.write:
            path.write_text(updated, encoding="utf-8")
        files_changed += 1
        calls_changed += len(edits)
        print(f"[rewrite] {path.relative_to(ROOT)} calls={len(edits)}")

    print(f"files_scanned={len(targets)}")
    print(f"files_rewritten={files_changed}")
    print(f"calls_scanned={calls_scanned}")
    print(f"calls_rewritten={calls_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
