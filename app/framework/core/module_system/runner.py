from __future__ import annotations

import importlib

from app.framework.core.module_system.injector import build_module_kwargs


def run_module(meta, global_config, runtime_context: dict):
    kwargs = build_module_kwargs(meta, global_config, runtime_context)
    return meta.runner(**kwargs)


def resolve_symbol(symbol_path: str):
    module_path, symbol_name = symbol_path.rsplit(":", 1)
    mod = importlib.import_module(module_path)
    return getattr(mod, symbol_name)


def run_module_class(module_class_path: str, automation=None, logger=None):
    module_class = resolve_symbol(module_class_path)
    return module_class(automation, logger).run()


def make_module_class(meta):
    if meta.module_class is not None:
        return meta.module_class

    if meta.generated_module_class is not None:
        return meta.generated_module_class

    from app.framework.infra.config.app_config import config

    class FunctionModuleAdapter:
        def __init__(self, auto, logger):
            self.auto = auto
            self.logger = logger

        def run(self):
            runtime_context = {
                "automation": self.auto,
                "logger": self.logger,
            }
            run_module(meta, config, runtime_context)

    FunctionModuleAdapter.__name__ = f"{meta.id.title().replace('_', '')}ModuleAdapter"
    meta.generated_module_class = FunctionModuleAdapter
    return FunctionModuleAdapter
