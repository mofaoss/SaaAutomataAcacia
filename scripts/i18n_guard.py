#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

LOGGER_LEVELS = {"info", "warning", "error"}
UI_TEXT_METHODS = {"setText", "setToolTip", "setPlaceholderText", "setWindowTitle"}
BANNED_HELPERS = {"t", "td"}
BANNED_DECL_FIELDS = {"en_name", "cn_name", "tw_name"}
MSGID_SEMANTIC_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
MSGID_HASHLIKE_RE = re.compile(r"^(?:[0-9a-f]{8,}|h[0-9a-f]{6,})$")
PLACEHOLDER_ASCII_PUNCT = set(" \t\r\n?!,.:;()[]{}-_/\\")
PLACEHOLDER_FULLWIDTH_ORDS = {0xFF01, 0xFF08, 0xFF09, 0xFF0C, 0xFF1A, 0xFF1B, 0xFF1F, 0x3002}


@dataclass
class Finding:
    kind: str
    path: str
    line: int
    message: str


def _changed_python_files() -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except Exception:
        return []

    files: list[Path] = []
    for raw in (proc.stdout or "").splitlines():
        if not raw:
            continue
        line = raw[3:]
        if " -> " in line:
            line = line.split(" -> ", 1)[1]
        p = ROOT / line.strip()
        if p.suffix == ".py" and p.exists():
            files.append(p)
    return sorted(set(files))




def _added_lines_map() -> dict[Path, set[int]]:
    try:
        proc = subprocess.run(
            ["git", "diff", "--unified=0", "--", "*.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except Exception:
        return {}

    result: dict[Path, set[int]] = {}
    current_file: Path | None = None

    for line in (proc.stdout or "").splitlines():
        if line.startswith("+++ b/"):
            rel = line[6:].strip()
            if rel.endswith(".py"):
                current_file = ROOT / rel
                result.setdefault(current_file, set())
            else:
                current_file = None
            continue

        if current_file is None or not line.startswith("@@"):
            continue

        # @@ -a,b +c,d @@
        try:
            plus = line.split(" +", 1)[1].split(" ", 1)[0]
            if "," in plus:
                start_s, count_s = plus.split(",", 1)
                start = int(start_s)
                count = int(count_s)
            else:
                start = int(plus)
                count = 1
            for ln in range(start, start + max(count, 0)):
                result[current_file].add(ln)
        except Exception:
            continue

    return result


def _all_python_files() -> list[Path]:
    files = list((ROOT / "app").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py"))
    return sorted(set(files))


def _changed_i18n_json_files() -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except Exception:
        return []

    files: list[Path] = []
    for raw in (proc.stdout or "").splitlines():
        if not raw:
            continue
        line = raw[3:]
        if " -> " in line:
            line = line.split(" -> ", 1)[1]
        p = ROOT / line.strip()
        rel = p.relative_to(ROOT).as_posix() if p.exists() else ""
        if p.suffix == ".json" and "/i18n/" in f"/{rel}" and p.exists():
            files.append(p)
    return sorted(set(files))


def _all_i18n_json_files() -> list[Path]:
    files = list((ROOT / "app").rglob("*.json"))
    return sorted([p for p in files if "/i18n/" in f"/{p.relative_to(ROOT).as_posix()}"])


def _is_unusable_translation_value(value: str) -> bool:
    stripped = str(value or "").strip()
    if not stripped:
        return False

    has_question = any(ch == "?" or ord(ch) == 0xFF1F for ch in stripped)
    if not has_question:
        return False

    for ch in stripped:
        if ch in PLACEHOLDER_ASCII_PUNCT:
            continue
        if ord(ch) in PLACEHOLDER_FULLWIDTH_ORDS:
            continue
        return False
    return True


def _scan_i18n_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return findings

    if not isinstance(payload, dict):
        return findings

    rel = str(path.relative_to(ROOT))
    for key, value in payload.items():
        if not isinstance(value, str):
            continue
        if _is_unusable_translation_value(value):
            findings.append(
                Finding(
                    "error",
                    rel,
                    1,
                    f"Unusable placeholder translation for key '{key}'",
                )
            )
        if key.endswith(".description") and "\\n" in value:
            findings.append(
                Finding(
                    "error",
                    rel,
                    1,
                    f"Description key '{key}' must use real newlines instead of literal \\n",
                )
            )

    return findings


def _is_logger_call(func: ast.AST) -> bool:
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in LOGGER_LEVELS:
        return False
    if isinstance(func.value, ast.Attribute) and func.value.attr == "logger":
        return True
    if isinstance(func.value, ast.Name) and func.value.id == "logger":
        return True
    return False


def _is_translated_call(node: ast.AST | None) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_":
        return True
    return False


def _is_legacy_ui_text_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in {"ui_text", "_ui_text"}
    if isinstance(func, ast.Attribute):
        return func.attr in {"ui_text", "_ui_text"}
    return False


def _is_raw_text_node(node: ast.AST | None) -> bool:
    if _is_translated_call(node):
        return False
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(node.value.strip())
    return isinstance(node, ast.JoinedStr)


def _extract_msg_arg(call: ast.Call) -> ast.AST | None:
    if call.args:
        return call.args[0]
    for kw in call.keywords:
        if kw.arg in {"msg", "message", "text"}:
            return kw.value
    return None


def _scan_file(path: Path, *, allowed_lines: set[int] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
    except Exception:
        return findings

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in BANNED_HELPERS:
            if allowed_lines is None or node.lineno in allowed_lines:
                findings.append(Finding("error", str(path.relative_to(ROOT)), node.lineno, f"Banned public helper '{node.name}'"))

        if isinstance(node, ast.Call):
            if _is_legacy_ui_text_call(node):
                if allowed_lines is None or node.lineno in allowed_lines:
                    findings.append(
                        Finding(
                            "warning",
                            str(path.relative_to(ROOT)),
                            node.lineno,
                            "Legacy ui_text/_ui_text call detected. Prefer _('中文') and use .format(...) for dynamic values.",
                        )
                    )

            if _is_logger_call(node.func):
                msg_node = _extract_msg_arg(node)
                if _is_raw_text_node(msg_node):
                    if allowed_lines is None or node.lineno in allowed_lines:
                        findings.append(
                            Finding(
                                "error",
                                str(path.relative_to(ROOT)),
                                node.lineno,
                                "Raw logger user-visible string should be wrapped with _()",
                            )
                        )

            if isinstance(node.func, ast.Attribute) and node.func.attr in UI_TEXT_METHODS:
                text_node = _extract_msg_arg(node)
                if _is_raw_text_node(text_node):
                    if allowed_lines is None or node.lineno in allowed_lines:
                        findings.append(
                            Finding(
                                "error",
                                str(path.relative_to(ROOT)),
                                node.lineno,
                                f"Raw UI text in {node.func.attr} should be wrapped with _()",
                            )
                        )


            for kw in node.keywords:
                if kw.arg == "msgid" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    msgid = kw.value.value.strip()
                    if MSGID_HASHLIKE_RE.fullmatch(msgid):
                        if allowed_lines is None or node.lineno in allowed_lines:
                            findings.append(
                                Finding(
                                    "error",
                                    str(path.relative_to(ROOT)),
                                    node.lineno,
                                    "msgid must be semantic snake_case; hash-like msgid is forbidden",
                                )
                            )
                    elif not MSGID_SEMANTIC_RE.fullmatch(msgid):
                        if allowed_lines is None or node.lineno in allowed_lines:
                            findings.append(
                                Finding(
                                    "error",
                                    str(path.relative_to(ROOT)),
                                    node.lineno,
                                    "msgid must be semantic snake_case (e.g. task_completed)",
                                )
                            )

            for kw in node.keywords:
                if kw.arg in BANNED_DECL_FIELDS and "features/modules" in str(path).replace("\\", "/"):
                    if allowed_lines is None or node.lineno in allowed_lines:
                        findings.append(
                            Finding(
                                "error",
                                str(path.relative_to(ROOT)),
                                node.lineno,
                                f"Do not introduce declaration field '{kw.arg}' in module code",
                            )
                        )

    # Suspicious central translation location for module/business text.
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("app/features/i18n/"):
        findings.append(Finding("error", rel, 1, "Centralized features i18n path is not allowed; use owner-local module i18n"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Guardrails for new i18n/logging debt")
    parser.add_argument("--all", action="store_true", help="Scan all Python files (default scans changed files only)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    files = _all_python_files() if args.all else _changed_python_files()
    if not files:
        files = _all_python_files() if args.all else []

    changed_line_map = _added_lines_map() if not args.all else {}

    findings: list[Finding] = []
    for path in files:
        allowed = None if args.all else changed_line_map.get(path, set())
        findings.extend(_scan_file(path, allowed_lines=allowed))

    i18n_files = _all_i18n_json_files() if args.all else _changed_i18n_json_files()
    for path in i18n_files:
        findings.extend(_scan_i18n_file(path))

    errors = [f for f in findings if f.kind == "error"]

    if args.json:
        print(
            json.dumps(
                {
                    "scanned_files": [str(p.relative_to(ROOT)) for p in files],
                    "error_count": len(errors),
                    "findings": [f.__dict__ for f in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"scanned_files={len(files)}")
        print(f"error_count={len(errors)}")
        for f in findings:
            print(f"[{f.kind}] {f.path}:{f.line} {f.message}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
