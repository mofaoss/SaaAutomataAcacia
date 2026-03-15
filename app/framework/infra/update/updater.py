from __future__ import annotations

import importlib


def _updater_module():
    return importlib.import_module("app.features.utils.updater")


def get_local_version(file_path="update_data.txt"):
    return _updater_module().get_local_version(file_path=file_path)


def get_best_update_candidate(repo_url: str, local_version: str):
    return _updater_module().get_best_update_candidate(
        repo_url,
        local_version,
    )


def get_app_root():
    return _updater_module().get_app_root()


def resolve_batch_dir(downloaded_path: str):
    return _updater_module().resolve_batch_dir(downloaded_path)


UpdateDownloadThread = _updater_module().UpdateDownloadThread


__all__ = [
    "UpdateDownloadThread",
    "get_app_root",
    "get_best_update_candidate",
    "get_local_version",
    "resolve_batch_dir",
]

