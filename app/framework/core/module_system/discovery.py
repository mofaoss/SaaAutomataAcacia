from __future__ import annotations

import importlib
import pkgutil


def discover_modules(package: str):
    pkg = importlib.import_module(package)
    if not hasattr(pkg, "__path__"):
        return

    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        leaf = name.rsplit(".", 1)[-1]
        if ".usecase." in name and leaf.endswith("_usecase"):
            importlib.import_module(name)
