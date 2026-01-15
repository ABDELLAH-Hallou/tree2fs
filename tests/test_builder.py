"""Tests for filesystem builder."""

import pytest
from pathlib import Path
from tree2fs.builder import FilesystemBuilder
from tree2fs.models import FileItem, Node


def test_builder_creates_directory(tmp_path):
    """Test creating a directory."""
    root_item = FileItem(filename="project/", level=0)
    root = Node(root_item)

    builder = FilesystemBuilder(tmp_path)
    builder.build(root)

    assert (tmp_path / "project").exists()
    assert (tmp_path / "project").is_dir()


def test_builder_creates_file(tmp_path):
    """Test creating a file."""
    root_item = FileItem(filename="project/", level=0)
    root = Node(root_item)

    file_item = FileItem(filename="README.md", level=1)
    file_node = Node(file_item)
    root.add_child(file_node)

    builder = FilesystemBuilder(tmp_path)
    builder.build(root)

    assert (tmp_path / "project" / "README.md").exists()
    assert (tmp_path / "project" / "README.md").is_file()


def test_builder_skip_root(tmp_path):
    """Test skipping root directory."""
    root_item = FileItem(filename="project/", level=0)
    root = Node(root_item)

    file_item = FileItem(filename="README.md", level=1)
    file_node = Node(file_item)
    root.add_child(file_node)

    builder = FilesystemBuilder(tmp_path)
    builder.build(root, skip_root=True)

    # Root should not be created
    assert not (tmp_path / "project").exists()
    # But file should be created directly in base_dir
    assert (tmp_path / "README.md").exists()


def test_builder_dry_run(tmp_path):
    """Test dry run mode."""
    root_item = FileItem(filename="project/", level=0)
    root = Node(root_item)

    builder = FilesystemBuilder(tmp_path, dry_run=True)
    dirs, files = builder.build(root)

    # Nothing should be created
    assert not (tmp_path / "project").exists()
    # But counters should work
    assert dirs == 1
    assert files == 0


def test_builder_summary(tmp_path):
    """Test builder summary."""
    root_item = FileItem(filename="project/", level=0)
    root = Node(root_item)

    file_item = FileItem(filename="README.md", level=1)
    file_node = Node(file_item)
    root.add_child(file_node)

    builder = FilesystemBuilder(tmp_path)
    builder.build(root)

    summary = builder.get_summary()
    assert summary["directories"] == 1
    assert summary["files"] == 1
    assert summary["total"] == 2
