from __future__ import annotations

import argparse
import ast
import locale
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PerfectBuild.prepare_build import cleanup_stage_dir, prepare_nuitka_stage


SMOKE_ROOT_BASE = ROOT / "runtime" / "temp" / "nuitka_prepare_smoke"
RUN_ID = os.environ.get("NPS_RUN_ID", f"run_{os.getpid()}_{int(time.time() * 1000)}")
SMOKE_ROOT = SMOKE_ROOT_BASE / RUN_ID
PROJECT_ROOT = SMOKE_ROOT / "project"
PROJECT_ENTRY = PROJECT_ROOT / "main.py"
STAGE_DIR_NAME = ".nuitka_stage"
EXPECTED_LINES = [
    "\u5ba2\u6237\u533a\u5927\u5c0f\uff1a1920x1080\uff081.778:1\uff09\uff0c\u7b26\u5408 16:9 \u6807\u51c6\u6bd4\u4f8b",
]

SAMPLE_SOURCE = """from __future__ import annotations

import logging
import sys

import app.framework.i18n.runtime as i18n_runtime

i18n_runtime._resolve_lang = lambda: "zh_CN"
i18n_runtime.load_i18n_catalogs()

from app.framework.i18n import _


class LogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return i18n_runtime.render_message(record.msg, context="log", levelno=record.levelno)


def build_logger() -> logging.Logger:
    logger = logging.getLogger("nuitka.prepare.smoke")
    logger.setLevel(logging.WARNING)
    logger.propagate = False
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LogFormatter())
    logger.addHandler(handler)
    return logger


class BaseTask:
    def __init__(self) -> None:
        self.logger = build_logger()

    def determine_screen_ratio(self) -> bool:
        client_width = 1920
        client_height = 1080

        actual_ratio = client_width / client_height
        target_ratio = 16 / 9
        tolerance = 0.05
        is_16_9 = abs(actual_ratio - target_ratio) <= (target_ratio * tolerance)

        status = (
            _("Meets", msgid="meets")
            if is_16_9
            else _("Does not meet", msgid="does_not_meet")
        )

        self.logger.warning(
            _(f"Client area size: {client_width}x{client_height} ({actual_ratio:.3f}:1), {status} 16:9 standard ratio", msgid="client_area_size_client_width_x_client_height_ac")
        )
        return is_16_9


def main() -> None:
    task = BaseTask()
    task.determine_screen_ratio()


if __name__ == "__main__":
    main()
"""


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _run_command(cmd: list[str], *, cwd: Path | None = None) -> CommandResult:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    current_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_entries = [str(ROOT)]
    if current_pythonpath:
        pythonpath_entries.append(current_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=False,
        env=env,
    )
    return CommandResult(
        returncode=proc.returncode,
        stdout=_decode_stream(proc.stdout),
        stderr=_decode_stream(proc.stderr),
    )


def _decode_stream(raw: bytes) -> str:
    for encoding in ("utf-8", locale.getpreferredencoding(False), "gbk"):
        if not encoding:
            continue
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def _normalize_output_lines(output: str) -> list[str]:
    lines: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.rstrip("\r").strip()
        if not line:
            continue
        # Strip ANSI escape sequences emitted by some third-party libraries.
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if "QFluentWidgets Pro is now released." in line:
            continue
        lines.append(line)
    return lines


def _run_program(path: Path, *, cwd: Path | None = None) -> list[str]:
    result = _run_command([sys.executable, str(path)], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Program failed: {path}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return _normalize_output_lines(result.stdout)


def _assert_expected(lines: list[str], label: str) -> None:
    if lines != EXPECTED_LINES:
        raise AssertionError(
            f"{label} output mismatch.\nexpected: {EXPECTED_LINES}\nactual:   {lines}"
        )


def _prepare_mock_project() -> None:
    if SMOKE_ROOT.exists():
        shutil.rmtree(SMOKE_ROOT)
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECT_ENTRY.write_text(SAMPLE_SOURCE, encoding="utf-8")


def _ensure_transformed(stage_entry: Path) -> None:
    transformed = stage_entry.read_text(encoding="utf-8")
    if "_(f" in transformed:
        raise AssertionError("Stage still contains dynamic _(f\"...\") after prepare_build.")
    if ".format(" not in transformed:
        raise AssertionError("Stage source does not contain .format(...) rewrite.")
    _assert_client_area_call_rewritten(transformed)


def _assert_client_area_call_rewritten(source: str) -> None:
    tree = ast.parse(source)
    found_target = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "warning":
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if not isinstance(first_arg, ast.Call):
            continue
        if not isinstance(first_arg.func, ast.Attribute) or first_arg.func.attr != "format":
            continue
        i18n_call = first_arg.func.value
        if not isinstance(i18n_call, ast.Call):
            continue
        if not isinstance(i18n_call.func, ast.Name) or i18n_call.func.id != "_":
            continue
        if not i18n_call.args or not isinstance(i18n_call.args[0], ast.Constant):
            continue

        template = i18n_call.args[0].value
        if not isinstance(template, str) or "Client area size:" not in template:
            continue

        msgid_kw = next((kw for kw in i18n_call.keywords if kw.arg == "msgid"), None)
        if not msgid_kw or not isinstance(msgid_kw.value, ast.Constant):
            raise AssertionError("client-area _(...) rewrite lost msgid keyword.")
        if msgid_kw.value.value != "client_area_size_client_width_x_client_height_ac":
            raise AssertionError("client-area _(...) rewrite changed msgid unexpectedly.")

        placeholder_keys = {kw.arg for kw in first_arg.keywords if kw.arg is not None}
        expected_keys = {"client_width", "client_height", "actual_ratio", "status"}
        if not expected_keys.issubset(placeholder_keys):
            raise AssertionError(
                f"client-area .format(...) missing keys. expected subset {expected_keys}, actual {placeholder_keys}"
            )
        found_target = True
        break

    if not found_target:
        raise AssertionError("Did not find rewritten logger.warning client-area call in staged source.")


def _maybe_run_nuitka(script_path: Path, output_dir: Path, *, standalone: bool) -> Path:
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--assume-yes-for-downloads",
        "--remove-output",
        "--no-pyi-file",
        "--zig",
        f"--output-dir={output_dir}",
        f"--include-data-dir={ROOT / 'resources' / 'i18n'}=resources/i18n",
    ]
    if standalone:
        cmd.append("--standalone")
    cmd.append(str(script_path))

    result = _run_command(cmd, cwd=script_path.parent)
    if result.returncode != 0:
        raise RuntimeError(
            "Nuitka build failed.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    exe_name = f"{script_path.stem}.exe"
    if standalone:
        exe_path = output_dir / f"{script_path.stem}.dist" / exe_name
    else:
        exe_path = output_dir / exe_name
    if not exe_path.exists():
        raise FileNotFoundError(f"Nuitka output not found: {exe_path}")
    return exe_path


def _run_executable(exe_path: Path) -> list[str]:
    result = _run_command([str(exe_path)], cwd=exe_path.parent)
    if result.returncode != 0:
        raise RuntimeError(
            f"Executable failed: {exe_path}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return _normalize_output_lines(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test prepare_build f-string rewrite with optional Nuitka compilation."
    )
    parser.add_argument(
        "--skip-nuitka",
        action="store_true",
        help="Only verify source + prepare stage behavior, skip Nuitka compile and run.",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Use --standalone mode for Nuitka (default is accelerated mode).",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help=f"Keep temp files for debugging (under {SMOKE_ROOT_BASE}).",
    )
    args = parser.parse_args()

    _prepare_mock_project()
    print(f"[1/5] mock project ready: {PROJECT_ROOT}")

    raw_lines = _run_program(PROJECT_ENTRY)
    _assert_expected(raw_lines, "raw python")
    print("[2/5] raw source run ok")

    stage_result = prepare_nuitka_stage(project_root=PROJECT_ROOT, stage_dir_name=STAGE_DIR_NAME)
    stage_entry = stage_result.stage_dir / "main.py"
    _ensure_transformed(stage_entry)
    stage_lines = _run_program(stage_entry, cwd=stage_result.stage_dir)
    _assert_expected(stage_lines, "prepared stage python")
    print(
        "[3/5] prepare stage run ok "
        f"(changed {stage_result.py_files_changed}/{stage_result.py_files_scanned}, "
        f"remaining dynamic={stage_result.remaining_dynamic_fstring_calls})"
    )

    if not args.skip_nuitka:
        build_root = SMOKE_ROOT / "build"
        src_out = build_root / "src"
        stage_out = build_root / "stage"
        src_exe = _maybe_run_nuitka(PROJECT_ENTRY, src_out, standalone=args.standalone)
        stage_exe = _maybe_run_nuitka(stage_entry, stage_out, standalone=args.standalone)

        src_exe_lines = _run_executable(src_exe)
        stage_exe_lines = _run_executable(stage_exe)
        _assert_expected(src_exe_lines, "nuitka raw exe")
        _assert_expected(stage_exe_lines, "nuitka prepared exe")
        if src_exe_lines != stage_exe_lines:
            raise AssertionError(
                "Nuitka outputs diverged between raw and prepare-stage sources.\n"
                f"raw exe: {src_exe_lines}\n"
                f"stage exe: {stage_exe_lines}"
            )
        print(f"[4/5] nuitka run ok (standalone={args.standalone})")
    else:
        print("[4/5] skipped nuitka by --skip-nuitka")

    print("[5/5] smoke test passed")
    return 0


if __name__ == "__main__":
    stage_dir = PROJECT_ROOT / STAGE_DIR_NAME
    try:
        raise SystemExit(main())
    finally:
        # Keep temp files only when explicit debugging is requested.
        keep = "--keep-temp" in sys.argv
        if not keep:
            try:
                cleanup_stage_dir(stage_dir)
            except Exception:
                pass
            if SMOKE_ROOT.exists():
                shutil.rmtree(SMOKE_ROOT, ignore_errors=True)
