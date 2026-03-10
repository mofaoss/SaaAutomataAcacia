from __future__ import annotations

from app.framework.application.modules.contracts import ModuleSpec
from app.framework.core.module_system import ModuleHost, get_modules_by_host, make_module_class


def _meta_to_spec(meta, host: ModuleHost) -> ModuleSpec:
    if meta.ui_factory is None and meta.page_cls is not None:
        meta.ui_factory = lambda parent, _host: meta.page_cls(parent)

    module_class = meta.module_class or make_module_class(meta)
    return ModuleSpec(
        id=meta.id,
        zh_name=meta.name,
        en_name=meta.en_name or meta.name,
        order=meta.order,
        hosts=(host,),
        ui_factory=meta.ui_factory,
        module_class=module_class,
        ui_bindings=meta.ui_bindings,
        passive=meta.passive,
    )


def get_periodic_module_specs() -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.PERIODIC)
    return [_meta_to_spec(meta, ModuleHost.PERIODIC) for meta in metas]


def get_on_demand_module_specs(*, include_passive: bool = True) -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.ON_DEMAND)
    if not include_passive:
        metas = [meta for meta in metas if not meta.passive]
    return [_meta_to_spec(meta, ModuleHost.ON_DEMAND) for meta in metas]
