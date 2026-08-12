"""Unit tests for agent.files.* (path safety, listing, delete)."""

from __future__ import annotations

import pytest

from agent.files import browser, delete


def test_resolve_safe_path_allows_paths_inside_root(tmp_path):
    (tmp_path / "sub").mkdir()
    resolved = browser.resolve_safe_path(str(tmp_path), "sub")
    assert resolved == (tmp_path / "sub").resolve()


def test_resolve_safe_path_blocks_traversal_outside_root(tmp_path):
    with pytest.raises(PermissionError):
        browser.resolve_safe_path(str(tmp_path), "../../etc/passwd")


def test_resolve_safe_path_blocks_absolute_path_outside_root(tmp_path):
    with pytest.raises(PermissionError):
        browser.resolve_safe_path(str(tmp_path), "/etc/passwd")


def test_resolve_safe_path_no_root_allows_any_absolute_path(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("hi")
    resolved = browser.resolve_safe_path(None, str(target))
    assert resolved == target.resolve()


def test_list_directory_returns_entries(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = browser.list_directory(str(tmp_path), ".")
    names = {entry["name"] for entry in result["entries"]}
    assert names == {"a.txt", "subdir"}


def test_list_directory_raises_for_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        browser.list_directory(str(tmp_path), "does-not-exist")


def test_list_directory_raises_for_file_not_directory(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("hi")
    with pytest.raises(NotADirectoryError):
        browser.list_directory(str(tmp_path), "a.txt")


def test_delete_file_removes_it(tmp_path):
    file_path = tmp_path / "to_delete.txt"
    file_path.write_text("bye")

    result = delete.execute(str(tmp_path), {"path": "to_delete.txt"})

    assert not file_path.exists()
    assert result["action"] == "delete_file"


def test_delete_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        delete.execute(str(tmp_path), {"path": "nope.txt"})


def test_delete_requires_path_in_payload(tmp_path):
    with pytest.raises(ValueError):
        delete.execute(str(tmp_path), {})
