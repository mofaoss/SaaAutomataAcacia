from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.framework.core.module_system.decorators import DEFAULT_SOURCE_LANG, SUPPORTED_LANGS

_CATALOGS: dict[str, dict[str, str]] = {lang: {} for lang in SUPPORTED_LANGS}
_LOADED = False


def _merge_file(lang: str, path: Path) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(data, dict):
        return
    _CATALOGS.setdefault(lang, {}).update({str(k): str(v) for k, v in data.items()})


def load_i18n_catalogs() -> None:
    global _LOADED
    root = Path(__file__).resolve().parents[3]

    framework_i18n = root / "app" / "framework" / "i18n"
    for lang in SUPPORTED_LANGS:
        _merge_file(lang, framework_i18n / f"{lang}.json")

    modules_root = root / "app" / "features" / "modules"
    if modules_root.exists():
        for module_dir in modules_root.iterdir():
            if not module_dir.is_dir():
                continue
            i18n_dir = module_dir / "i18n"
            if not i18n_dir.exists():
                continue
            for lang in SUPPORTED_LANGS:
                _merge_file(lang, i18n_dir / f"{lang}.json")
    _LOADED = True


def _resolve_lang() -> str:
    try:
        from app.framework.infra.config.app_config import is_non_chinese_ui_language

        return "en" if is_non_chinese_ui_language() else "zh_CN"
    except Exception:
        return DEFAULT_SOURCE_LANG


def tr(key: str, fallback: str | None = None, **kwargs: Any) -> str:
    if not _LOADED:
        load_i18n_catalogs()

    lang = _resolve_lang()
    source = DEFAULT_SOURCE_LANG

    value = (
        _CATALOGS.get(lang, {}).get(key)
        or _CATALOGS.get(source, {}).get(key)
        or fallback
        or key
    )
    try:
        return value.format(**kwargs)
    except Exception:
        return value


def get_catalog(lang: str) -> dict[str, str]:
    if not _LOADED:
        load_i18n_catalogs()
    return dict(_CATALOGS.get(lang, {}))
