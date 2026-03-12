#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import copy
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PerfectBuild.ast_i18n_transformer import I18nFStringTransformer

TARGET_FUNC_NAMES = {"ui_text", "_ui_text"}
ZH_KEYWORDS = {"zh", "zh_text", "cn", "cn_text", "chinese"}


@dataclass
class Edit:
    start: int
    end: int
    replacement: str


@dataclass
class FileReport:
    path: Path
    rewrites: int
    skipped: int
    changed: bool


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    cursor = 0
    for line in text.splitlines(keepends=True):
        cursor += len(line.encode("utf-8"))
        offsets.append(cursor)
    return offsets


def _to_offset(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[lineno - 1] + col


def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _is_target_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in TARGET_FUNC_NAMES
    if isinstance(func, ast.Attribute):
        return func.attr in TARGET_FUNC_NAMES
    return False


def _is_wrapped_by_gettext(node: ast.Call, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    if not isinstance(parent, ast.Call):
        return False
    if not isinstance(parent.func, ast.Name) or parent.func.id != "_":
        return False
    return any(arg is node for arg in parent.args)


def _extract_source_arg(node: ast.Call) -> ast.AST | None:
    for kw in node.keywords:
        if kw.arg in ZH_KEYWORDS:
            return kw.value
    # ui_text/_ui_text legacy shape is usually (zh, en), so prefer arg[0].
    if len(node.args) >= 1:
        return node.args[0]
    return None


def _build_replacement_expr(source_arg: ast.AST) -> ast.AST:
    if isinstance(source_arg, ast.Constant) and isinstance(source_arg.value, str) and source_arg.value == "":
        return ast.Constant(value="")

    # Legacy intermediate form: _(zh, en) or _(zh, en).format(...)
    if (
        isinstance(source_arg, ast.Call)
        and isinstance(source_arg.func, ast.Name)
        and source_arg.func.id == "_"
        and len(source_arg.args) >= 1
    ):
        return _build_replacement_expr(source_arg.args[0])

    if (
        isinstance(source_arg, ast.Call)
        and isinstance(source_arg.func, ast.Attribute)
        and source_arg.func.attr == "format"
        and isinstance(source_arg.func.value, ast.Call)
        and isinstance(source_arg.func.value.func, ast.Name)
        and source_arg.func.value.func.id == "_"
        and len(source_arg.func.value.args) >= 1
    ):
        base = _build_replacement_expr(source_arg.func.value.args[0])
        return ast.Call(
            func=ast.Attribute(value=base, attr="format", ctx=ast.Load()),
            args=[copy.deepcopy(arg) for arg in source_arg.args],
            keywords=[copy.deepcopy(kw) for kw in source_arg.keywords],
        )

    if isinstance(source_arg, ast.Call) and isinstance(source_arg.func, ast.Name) and source_arg.func.id == "_":
        return copy.deepcopy(source_arg)

    base_call = ast.Call(
        func=ast.Name(id="_", ctx=ast.Load()),
        args=[copy.deepcopy(source_arg)],
        keywords=[],
    )

    if isinstance(source_arg, (ast.JoinedStr, ast.BinOp)):
        helper = I18nFStringTransformer()
        rewritten = helper._rewrite_i18n_dynamic_call(base_call, copy.deepcopy(source_arg))
        if isinstance(rewritten, ast.Call):
            return rewritten

    return base_call


def _collect_edits(source: str, tree: ast.AST) -> tuple[list[Edit], int]:
    parents = _build_parent_map(tree)
    offsets = _line_offsets(source)
    edits: list[Edit] = []
    skipped = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _is_target_call(node):
            continue
        if _is_wrapped_by_gettext(node, parents):
            skipped += 1
            continue
        source_arg = _extract_source_arg(node)
        if source_arg is None:
            skipped += 1
            continue
        if not hasattr(node, "end_lineno") or not hasattr(node, "end_col_offset"):
            skipped += 1
            continue

        replacement_expr = _build_replacement_expr(source_arg)
        replacement_text = ast.unparse(replacement_expr)

        start = _to_offset(offsets, int(node.lineno), int(node.col_offset))
        end = _to_offset(offsets, int(node.end_lineno), int(node.end_col_offset))
        edits.append(Edit(start=start, end=end, replacement=replacement_text))

    edits.sort(key=lambda item: item.start, reverse=True)
    return edits, skipped


def _apply_edits(source: str, edits: list[Edit]) -> str:
    updated = source.encode("utf-8")
    for edit in edits:
        updated = (
            updated[: edit.start]
            + edit.replacement.encode("utf-8")
            + updated[edit.end :]
        )
    return updated.decode("utf-8")


def process_file(path: Path, *, write: bool) -> FileReport:
    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return FileReport(path=path, rewrites=0, skipped=0, changed=False)

    edits, skipped = _collect_edits(source, tree)
    if not edits:
        return FileReport(path=path, rewrites=0, skipped=skipped, changed=False)

    updated = _apply_edits(source, edits)
    if updated == source:
        return FileReport(path=path, rewrites=0, skipped=skipped, changed=False)

    # Ensure transformed file remains valid Python.
    ast.parse(updated, filename=str(path))

    if write:
        path.write_text(updated, encoding="utf-8")

    return FileReport(path=path, rewrites=len(edits), skipped=skipped, changed=True)


def _iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix == ".py":
            files.append(p)
            continue
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate ui_text/_ui_text usage to gettext _() calls."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write transformed code back to disk.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["app"],
        help="Files or directories to scan (default: app).",
    )
    args = parser.parse_args()

    paths = [(ROOT / p).resolve() if not Path(p).is_absolute() else Path(p) for p in args.paths]
    files = _iter_python_files(paths)

    rewritten_files = 0
    rewritten_calls = 0
    skipped_calls = 0

    for path in files:
        report = process_file(path, write=args.write)
        if report.changed:
            rewritten_files += 1
            rewritten_calls += report.rewrites
            print(f"[rewrite] {path.relative_to(ROOT)} calls={report.rewrites} skipped={report.skipped}")
        skipped_calls += report.skipped

    print(f"files_scanned={len(files)}")
    print(f"files_rewritten={rewritten_files}")
    print(f"calls_rewritten={rewritten_calls}")
    print(f"calls_skipped={skipped_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
