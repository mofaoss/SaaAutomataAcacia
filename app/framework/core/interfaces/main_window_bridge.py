from __future__ import annotations

from typing import Any, Protocol


class MainWindowFeatureBridge(Protocol):
    """Framework-facing composition root contract for MainWindow."""

    def configure_module_registry(self) -> None:
        ...

    def create_home_interface(self, window: Any):
        ...

    def create_additional_interface(self, window: Any):
        ...

    def initialize_ocr_module(self):
        ...

