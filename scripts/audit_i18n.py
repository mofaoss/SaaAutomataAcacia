#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.framework.core.module_system.decorators import DEFAULT_SOURCE_LANG, SUPPORTED_LANGS


def _audit_framework() -> list[str]:
    base = ROOT / "app" / "framework" / "i18n"
    lines = ["[framework]"]
    missing = [lang for lang in SUPPORTED_LANGS if not (base / f"{lang}.json").exists()]
    if missing:
        lines.append(f"  source_lang: {DEFAULT_SOURCE_LANG}")
        lines.append(f"  missing: {', '.join(missing)}")
    else:
        lines.append("  missing: none")
    return lines


def _audit_modules() -> list[str]:
    modules_root = ROOT / "app" / "features" / "modules"
    lines = ["[modules]"]
    for module_dir in sorted([p for p in modules_root.iterdir() if p.is_dir()], key=lambda p: p.name):
        if module_dir.name.startswith("__"):
            continue
        i18n_dir = module_dir / "i18n"
        missing = [lang for lang in SUPPORTED_LANGS if not (i18n_dir / f"{lang}.json").exists()]
        lines.append(f"{module_dir.name}:")
        lines.append(f"  source_lang: {DEFAULT_SOURCE_LANG}")
        lines.append(f"  missing: {', '.join(missing) if missing else 'none'}")
    return lines


def main() -> int:
    output = []
    output.extend(_audit_framework())
    output.append("")
    output.extend(_audit_modules())
    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
