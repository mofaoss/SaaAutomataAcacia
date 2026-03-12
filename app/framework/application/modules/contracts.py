from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Literal

from app.framework.application.modules.name_resolver import resolve_display_name


class HostContext(str, Enum):
    PERIODIC = "periodic"
    ON_DEMAND = "on_demand"


@dataclass(frozen=True)
class ModuleUiBindings:
    page_attr: str
    start_button_attr: Optional[str] = None
    card_widget_attr: Optional[str] = None
    log_widget_attr: Optional[str] = None


@dataclass(frozen=True)
class ModuleSpec:
    id: str
    name: str
    name_msgid: str
    order: int
    hosts: tuple[HostContext, ...]
    ui_factory: Callable[[object, HostContext], object]
    module_class: Optional[type] = None
    ui_bindings: Optional[ModuleUiBindings] = None
    passive: bool = False
    on_demand_execution: Literal["exclusive", "background"] = "exclusive"
    on_demand_background_keys: tuple[str, ...] = ()

    def get_display_name(self) -> str:
        return resolve_display_name(
            name=str(self.name or ""),
            name_msgid=str(self.name_msgid or ""),
            fallback_id=self.id,
        )

    def supports(self, host: HostContext) -> bool:
        return host in self.hosts

    def get_name(self, is_non_chinese_ui: bool) -> str:
        return self.get_display_name()
