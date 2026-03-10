from __future__ import annotations

from scripts.ui_sync import _summarize_severity


def test_ui_sync_severity_counts_must_fix_and_advisory():
    summary = {
        "unresolved_references": 2,
        "new_definitions": 1,
        "missing_assets": 3,
        "locale_gaps": 0,
        "duplicate_ids": 1,
        "source_manifest_missing": 0,
        "missing_name": 2,
        "stale_entries": 4,
        "conflicting_defaults": 1,
        "roi_drift": 5,
    }
    sev = _summarize_severity(summary)
    assert sev["must_fix_count"] == 9
    assert sev["advisory_count"] == 10

