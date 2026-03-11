from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def _is_usecase_module_name(name: str) -> bool:
    leaf = name.rsplit(".", 1)[-1]
    return ".usecase." in name and leaf.endswith("_usecase")


def _discover_by_pkgutil(pkg) -> list[str]:
    imported: list[str] = []
    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if not _is_usecase_module_name(name):
            continue
        importlib.import_module(name)
        imported.append(name)
    return imported


def _discover_by_filesystem(pkg) -> list[str]:
    imported: list[str] = []
    seen: set[str] = set()
    for base in getattr(pkg, "__path__", []):
        base_path = Path(base)
        if not base_path.exists():
            continue
        for py in base_path.rglob("*_usecase.py"):
            if "__pycache__" in py.parts:
                continue
            if "usecase" not in py.parts:
                continue
            rel = py.relative_to(base_path).with_suffix("")
            module_name = pkg.__name__ + "." + ".".join(rel.parts)
            if module_name in seen or not _is_usecase_module_name(module_name):
                continue
            importlib.import_module(module_name)
            seen.add(module_name)
            imported.append(module_name)
    return imported


def discover_modules(package: str):
    pkg = importlib.import_module(package)
    if not hasattr(pkg, "__path__"):
        return

    # In packaged environments pkgutil enumeration can be partial.
    # Always execute both strategies and rely on Python import cache for deduplication.
    _discover_by_pkgutil(pkg)
    _discover_by_filesystem(pkg)

