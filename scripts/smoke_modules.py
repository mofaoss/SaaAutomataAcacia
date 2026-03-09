#!/usr/bin/env python
# coding:utf-8
from __future__ import annotations

import importlib
import inspect
import multiprocessing as mp
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ERROR_TYPES = {"ModuleNotFoundError", "ImportError", "NameError"}


class DummyLogger:
    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


class DummyCallable:
    def __call__(self, *args, **kwargs):
        return False

    def __getattr__(self, _):
        return self

    def __bool__(self):
        return False


class DummyAuto:
    scale_x = 1.0
    scale_y = 1.0

    def __init__(self):
        self._fallback = DummyCallable()

    def take_screenshot(self, *args, **kwargs):
        return None

    def click_element(self, *args, **kwargs):
        return False

    def find_element(self, *args, **kwargs):
        return False

    def click_element_with_pos(self, *args, **kwargs):
        return False

    def press_key(self, *args, **kwargs):
        return None

    def type_string(self, *args, **kwargs):
        return None

    def move_click(self, *args, **kwargs):
        return False

    def find_target_near_source(self, *args, **kwargs):
        return False

    def __getattr__(self, _):
        return self._fallback


@dataclass
class CheckResult:
    host: str
    module_id: str
    module_path: str
    class_name: str
    ui_ok: bool
    ui_error_type: str | None
    ui_error: str | None
    run_status: str
    run_error_type: str | None
    run_error: str | None

    @property
    def has_reference_error(self) -> bool:
        return (self.ui_error_type in REFERENCE_ERROR_TYPES) or (
            self.run_error_type in REFERENCE_ERROR_TYPES
        )


def _build_ctor_kwargs(cls: type) -> dict[str, Any]:
    sig = inspect.signature(cls.__init__)
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        lname = name.lower()
        if "auto" in lname:
            kwargs[name] = DummyAuto()
        elif "logger" in lname or lname in {"log"}:
            kwargs[name] = DummyLogger()
        elif param.default is not inspect._empty:
            continue
        else:
            kwargs[name] = None
    return kwargs


def _run_module_worker(module_path: str, class_name: str, queue: mp.Queue):
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        kwargs = _build_ctor_kwargs(cls)
        instance = cls(**kwargs)

        run_method = getattr(instance, "run", None)
        if callable(run_method):
            run_method()
            queue.put({"status": "finished"})
            return
        queue.put({"status": "no_run"})
    except Exception as exc:  # noqa: BLE001
        queue.put(
            {
                "status": "error",
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )


def _check_ui(spec, host_ctx) -> tuple[bool, str | None, str | None]:
    try:
        from PySide6.QtWidgets import QApplication, QWidget

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        parent = QWidget()
        page = spec.ui_factory(parent, host_ctx)
        if hasattr(page, "bind_host_context"):
            page.bind_host_context(host_ctx)
        page.deleteLater()
        parent.deleteLater()
        app.processEvents()
        return True, None, None
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__, str(exc)


def _check_run(module_path: str, class_name: str, timeout_sec: int = 4) -> tuple[str, str | None, str | None]:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(
        target=_run_module_worker,
        args=(module_path, class_name, queue),
        daemon=True,
    )
    proc.start()
    proc.join(timeout_sec)

    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        return "timeout", None, None

    if queue.empty():
        return "error", "UnknownError", "Child process exited without result"

    result = queue.get()
    status = result.get("status")
    if status in {"finished", "no_run"}:
        return status, None, None
    return "error", result.get("type"), result.get("message")


def collect_specs():
    from app.framework.application.modules import HostContext, get_on_demand_module_specs, get_periodic_module_specs

    specs = []
    for spec in get_periodic_module_specs():
        specs.append(("periodic", HostContext.PERIODIC, spec))
    for spec in get_on_demand_module_specs(include_passive=True):
        specs.append(("on_demand", HostContext.ON_DEMAND, spec))
    return specs


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    seen_run_targets: set[tuple[str, str]] = set()

    for host_name, host_ctx, spec in collect_specs():
        module_cls = spec.module_class
        module_path = module_cls.__module__ if module_cls is not None else "-"
        class_name = module_cls.__name__ if module_cls is not None else "-"

        ui_ok, ui_err_type, ui_err = _check_ui(spec, host_ctx)

        run_status = "skipped"
        run_err_type = None
        run_err = None
        if module_cls is not None:
            run_key = (module_path, class_name)
            if run_key in seen_run_targets:
                run_status = "deduplicated"
            else:
                seen_run_targets.add(run_key)
                run_status, run_err_type, run_err = _check_run(module_path, class_name)

        results.append(
            CheckResult(
                host=host_name,
                module_id=spec.id,
                module_path=module_path,
                class_name=class_name,
                ui_ok=ui_ok,
                ui_error_type=ui_err_type,
                ui_error=ui_err,
                run_status=run_status,
                run_error_type=run_err_type,
                run_error=run_err,
            )
        )
    return results


def print_report(results: list[CheckResult]) -> None:
    print("=== Module Smoke Check ===")
    for item in results:
        ui_flag = "OK" if item.ui_ok else f"FAIL({item.ui_error_type})"
        run_flag = item.run_status
        if item.run_error_type:
            run_flag += f"({item.run_error_type})"
        print(f"[{item.host}] {item.module_id:<20} UI={ui_flag:<20} RUN={run_flag}")
        if item.ui_error:
            print(f"  ui_error: {item.ui_error}")
        if item.run_error:
            print(f"  run_error: {item.run_error}")

    ref_errors = [r for r in results if r.has_reference_error]
    ui_failures = [r for r in results if not r.ui_ok]
    run_errors = [r for r in results if r.run_status == "error"]
    print("\n=== Summary ===")
    print(f"modules_total: {len(results)}")
    print(f"ui_failures: {len(ui_failures)}")
    print(f"run_errors: {len(run_errors)}")
    print(f"reference_errors: {len(ref_errors)}")


def main() -> int:
    import os
    import sys

    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    mp.freeze_support()
    try:
        mp.set_start_method("spawn")
    except RuntimeError:
        pass

    results = run_checks()
    print_report(results)

    has_reference_error = any(r.has_reference_error for r in results)
    return 1 if has_reference_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
