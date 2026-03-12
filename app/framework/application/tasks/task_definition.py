# coding:utf-8
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TaskDomain(str, Enum):
    DAILY = "daily"
    ADDITIONAL = "additional"
    # Preferred semantic aliases.
    PERIODIC = "daily"
    ON_DEMAND = "additional"


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    module_class: type
    name: str
    name_msgid: str
    domain: TaskDomain
    ui_page_index: Optional[int] = None
    option_key: Optional[str] = None
    page_attr: Optional[str] = None
    card_widget_attr: Optional[str] = None
    log_widget_attr: Optional[str] = None
    start_button_attr: Optional[str] = None
    requires_home_sync: bool = True
    is_mandatory: bool = False
    force_first: bool = False

    def to_legacy_meta(self) -> dict:
        return {
            "module_class": self.module_class,
            "ui_page_index": self.ui_page_index,
            "option_key": self.option_key,
            "name": self.name,
            "name_msgid": self.name_msgid,
            "requires_home_sync": self.requires_home_sync,
            "is_mandatory": self.is_mandatory,
            "force_first": self.force_first,
        }
