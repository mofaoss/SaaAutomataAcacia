from __future__ import annotations

from app.framework.application.modules.contracts import ModuleSpec, ModuleUiBindings
from app.framework.core.module_system import ModuleHost, get_modules_by_host, make_module_class


def _meta_to_spec(meta, host: ModuleHost) -> ModuleSpec:
    if meta.ui_factory is None:
        if meta.page_cls is not None:
            meta.ui_factory = lambda parent, _host: meta.page_cls(parent)
        else:
            from app.framework.ui.auto_page.factory import build_auto_page

            meta.ui_factory = lambda parent, host_ctx, _meta=meta: build_auto_page(parent, module_meta=_meta, host_context=host_ctx)

    if meta.ui_bindings is None:
        meta.ui_bindings = ModuleUiBindings(
            page_attr=f"page_{meta.id}",
            start_button_attr="PushButton_start",
            card_widget_attr="SimpleCardWidget_option",
            log_widget_attr="textBrowser_log",
        )

    module_class = meta.module_class or make_module_class(meta)
    resolved_name_msgid = str(getattr(meta, "name_msgid", "") or f"module.{meta.id}.title").strip()
    return ModuleSpec(
        id=meta.id,
        name=str(getattr(meta, "name", "") or ""),
        name_msgid=resolved_name_msgid,
        order=meta.order,
        hosts=(host,),
        ui_factory=meta.ui_factory,
        module_class=module_class,
        ui_bindings=meta.ui_bindings,
        passive=meta.passive,
        on_demand_execution=getattr(meta, "on_demand_execution", "exclusive"),
        on_demand_background_keys=getattr(meta, "on_demand_background_keys", ()),
    )


def get_periodic_module_specs() -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.PERIODIC)
    return [_meta_to_spec(meta, ModuleHost.PERIODIC) for meta in metas]


def get_on_demand_module_specs(*, include_passive: bool = True) -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.ON_DEMAND)
    if not include_passive:
        metas = [meta for meta in metas if not meta.passive]
    return [_meta_to_spec(meta, ModuleHost.ON_DEMAND) for meta in metas]

