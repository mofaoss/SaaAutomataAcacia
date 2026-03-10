from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ModuleHost(str, Enum):
    PERIODIC = "periodic"
    ON_DEMAND = "on_demand"


@dataclass(slots=True)
class ModuleMeta:
    id: str
    name: str
    host: ModuleHost
    runner: Callable[..., Any]

    page_cls: type | None = None
    ui_factory: Callable[[object, ModuleHost], object] | None = None
    module_class: type | None = None
    ui_bindings: Any = None

    order: int = 100
    description: str = ""
    enabled: bool = True
    passive: bool = False

    en_name: str = ""

    periodic_enabled_by_default: bool = False
    periodic_mandatory: bool = False
    periodic_force_first: bool = False
    periodic_default_hour: int = 4
    periodic_default_minute: int = 0
    periodic_max_runs: int = 1
    periodic_requires_home_sync: bool = True
    periodic_ui_page_index: int | None = None
    periodic_option_key: str | None = None
    periodic_default_activation_config: list[dict[str, Any]] = field(default_factory=list)

    config_schema: list[dict[str, Any]] = field(default_factory=list)
    generated_module_class: type | None = None

    def display_name(self, is_non_chinese_ui: bool) -> str:
        if is_non_chinese_ui and self.en_name:
            return self.en_name
        return self.name
