from __future__ import annotations

import argparse
import os
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


RUN_ID = f"client_area_case_{os.getpid()}_{int(time.time() * 1000)}"
TEMP_ROOT = ROOT / "runtime" / "temp" / RUN_ID
RUNNER_REL = Path("runtime") / "temp" / RUN_ID / "client_area_case_runner.py"
RUNNER_PATH = ROOT / RUNNER_REL
STAGE_DIR_NAME = ".nuitka_stage_client_area_case"

EXPECTED_ZH_LINE = "客户区大小：1920x1080（1.778:1），符合 16:9 标准比例"
EXPECTED_RESULT_LINE = "CASE_RESULT::True"

RUNNER_SOURCE = """from __future__ import annotations

import logging
import types
import sys
from pathlib import Path

import win32gui

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.framework.i18n.runtime as i18n_runtime
from app.framework.i18n.runtime import render_message
from app.framework.core.task_engine.base_task import BaseTask, logger as base_logger

# Force zh_CN for deterministic assertions.
i18n_runtime._resolve_lang = lambda: "zh_CN"  # type: ignore[assignment]


class PlainI18nLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = render_message(record.msg, context="log", levelno=record.levelno)
        return str(rendered)


def _fake_get_client_rect(_hwnd: int):
    return (0, 0, 1920, 1080)


def main() -> None:
    win32gui.GetClientRect = _fake_get_client_rect  # type: ignore[assignment]

    handler = logging.StreamHandler()
    handler.setFormatter(PlainI18nLogFormatter())
    base_logger.handlers = [handler]
    base_logger.propagate = False
    base_logger.setLevel(logging.DEBUG)

    task = BaseTask()
    task.auto = types.SimpleNamespace(hwnd=123, scale_x=None, scale_y=None)
    ok = task.determine_screen_ratio(task.auto.hwnd)
    print(f"CASE_RESULT::{ok}")


if __name__ == "__main__":
    main()
"""


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _run(cmd: list[str], *, cwd: Path | None = None) -> CommandResult:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def _extract_lines(stdout: str, stderr: str) -> list[str]:
    merged = f"{stdout}\n{stderr}"
    return [line.strip() for line in merged.splitlines() if line.strip()]


def _has_expected(lines: list[str]) -> bool:
    return EXPECTED_ZH_LINE in lines and EXPECTED_RESULT_LINE in lines


def _find_case_line(lines: list[str]) -> str:
    for line in lines:
        if "Client area size:" in line or "客户区大小：" in line:
            return line
    return "<missing>"


def _ensure_stage_rewrite(stage_dir: Path) -> None:
    stage_base_task = stage_dir / "app" / "framework" / "core" / "task_engine" / "base_task.py"
    text = stage_base_task.read_text(encoding="utf-8")
    marker = "client_area_size_client_width_x_client_height_ac"
    idx = text.find(marker)
    if idx < 0:
        raise AssertionError("stage base_task.py does not contain target msgid")
    window = text[max(0, idx - 260): idx + 260]
    if ".format(" not in window:
        raise AssertionError("stage rewrite check failed: expected .format(...) near target msgid")


def _build_nuitka(stage_runner: Path, stage_dir: Path, output_dir: Path, *, standalone: bool) -> Path:
    i18n_src = stage_dir / "resources" / "i18n"
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--assume-yes-for-downloads",
        "--remove-output",
        "--no-pyi-file",
        "--zig",
        f"--output-dir={output_dir}",
        f"--include-data-dir={i18n_src}=resources/i18n",
    ]
    if standalone:
        cmd.append("--standalone")
    cmd.append(str(stage_runner))

    result = _run(cmd, cwd=stage_dir)
    if result.returncode != 0:
        raise RuntimeError(
            "Nuitka build failed.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    exe_name = f"{stage_runner.stem}.exe"
    exe_path = (output_dir / f"{stage_runner.stem}.dist" / exe_name) if standalone else (output_dir / exe_name)
    if not exe_path.exists():
        raise FileNotFoundError(f"Nuitka output not found: {exe_path}")
    return exe_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test BaseTask client-area i18n log through prepare_build + Nuitka package flow."
    )
    parser.add_argument("--skip-nuitka", action="store_true", help="Skip Nuitka compile/run, only verify source+stage.")
    parser.add_argument("--standalone", action="store_true", help="Use Nuitka standalone mode.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temp files for debugging.")
    args = parser.parse_args()

    if TEMP_ROOT.exists():
        shutil.rmtree(TEMP_ROOT, ignore_errors=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    RUNNER_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNNER_PATH.write_text(RUNNER_SOURCE, encoding="utf-8")
    print(f"[1/6] runner ready: {RUNNER_PATH}")

    src = _run([sys.executable, str(RUNNER_PATH)], cwd=ROOT)
    if src.returncode != 0:
        raise RuntimeError(f"source run failed:\nstdout:\n{src.stdout}\nstderr:\n{src.stderr}")
    source_lines = _extract_lines(src.stdout, src.stderr)
    if not _has_expected(source_lines):
        raise AssertionError(
            "source run did not emit expected Chinese log.\n"
            f"expected={EXPECTED_ZH_LINE}\nactual={source_lines}"
        )
    print("[2/6] source run passed")

    stage_result = prepare_nuitka_stage(project_root=ROOT, stage_dir_name=STAGE_DIR_NAME)
    _ensure_stage_rewrite(stage_result.stage_dir)
    stage_runner = stage_result.stage_dir / RUNNER_REL
    if not stage_runner.exists():
        raise FileNotFoundError(f"staged runner not found: {stage_runner}")
    print(
        "[3/6] prepare stage passed "
        f"(changed {stage_result.py_files_changed}/{stage_result.py_files_scanned}, "
        f"remaining_dynamic={stage_result.remaining_dynamic_fstring_calls})"
    )

    staged = _run([sys.executable, str(stage_runner)], cwd=stage_result.stage_dir)
    if staged.returncode != 0:
        raise RuntimeError(f"stage run failed:\nstdout:\n{staged.stdout}\nstderr:\n{staged.stderr}")
    stage_lines = _extract_lines(staged.stdout, staged.stderr)
    stage_ok = _has_expected(stage_lines)
    print(f"[4/6] staged source run done: ok={stage_ok} line={_find_case_line(stage_lines)}")

    if args.skip_nuitka:
        print("[5/6] skip nuitka")
        if not stage_ok:
            raise AssertionError("stage run did not preserve Chinese log translation")
        print("[6/6] case test passed")
        return 0

    build_dir = TEMP_ROOT / "nuitka_build"
    exe = _build_nuitka(stage_runner, stage_result.stage_dir, build_dir, standalone=args.standalone)
    print(f"[5/6] nuitka build passed: {exe}")

    run_exe = _run([str(exe)], cwd=exe.parent)
    if run_exe.returncode != 0:
        raise RuntimeError(f"exe run failed:\nstdout:\n{run_exe.stdout}\nstderr:\n{run_exe.stderr}")
    exe_lines = _extract_lines(run_exe.stdout, run_exe.stderr)
    exe_ok = _has_expected(exe_lines)
    print(f"[6/6] nuitka runtime run done: ok={exe_ok} line={_find_case_line(exe_lines)}")
    if not stage_ok or not exe_ok:
        raise AssertionError(
            "translation regression detected.\n"
            f"stage_line={_find_case_line(stage_lines)}\n"
            f"exe_line={_find_case_line(exe_lines)}"
        )
    return 0


if __name__ == "__main__":
    stage_dir = ROOT / STAGE_DIR_NAME
    keep = "--keep-temp" in sys.argv
    try:
        raise SystemExit(main())
    finally:
        if not keep:
            try:
                cleanup_stage_dir(stage_dir)
            except Exception:
                pass
            if TEMP_ROOT.exists():
                shutil.rmtree(TEMP_ROOT, ignore_errors=True)
