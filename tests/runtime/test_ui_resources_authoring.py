from __future__ import annotations

from app.framework.ui_resources import U
from app.framework.ui_resources.models import UIDefinition, UIReference


def test_u_returns_reference_for_short_id():
    ref = U("start")
    assert isinstance(ref, UIReference)
    assert ref.id == "start"


def test_u_returns_definition_for_inline_definition_style():
    item = U("开始", id="start", roi=(0.1, 0.2, 0.3, 0.4))
    assert isinstance(item, UIDefinition)
    assert item.id == "start"
    assert item.kind == "text"
    assert item.roi == (0.1, 0.2, 0.3, 0.4)

