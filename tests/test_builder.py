"""Extended tests for FilesystemBuilder."""

import pytest
from pathlib import Path

from tree2fs.builder import FilesystemBuilder
from tree2fs.models.file_item import FileItem
from tree2fs.models.node import Node


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_node(filename, level):
    return Node(data=FileItem(filename=filename, level=level))


def simple_tree(tmp_path):
    """Return a tree: project/ → [README.md, src/ → [main.py]]"""
    root = make_node("project/", 0)
    readme = make_node("README.md", 1)
    src = make_node("src/", 1)
    main = make_node("main.py", 2)
    root.add_child(readme)
    root.add_child(src)
    src.add_child(main)
    return root


# ---------------------------------------------------------------------------
# FilesystemBuilder tests
# ---------------------------------------------------------------------------

class TestFilesystemBuilderCreation:
    """Tests verifying files & directories are actually created."""

    def test_creates_root_directory(self, tmp_path):
        root = make_node("project/", 0)
        FilesystemBuilder(tmp_path).build(root)
        assert (tmp_path / "project").is_dir()

    def test_creates_nested_directory(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path).build(root)
        assert (tmp_path / "project" / "src").is_dir()

    def test_creates_file(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path).build(root)
        assert (tmp_path / "project" / "README.md").is_file()

    def test_creates_nested_file(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path).build(root)
        assert (tmp_path / "project" / "src" / "main.py").is_file()

    def test_return_value_counts(self, tmp_path):
        root = simple_tree(tmp_path)
        dirs, files = FilesystemBuilder(tmp_path).build(root)
        assert dirs == 2   # project/, src/
        assert files == 2  # README.md, main.py

    def test_create_deeply_nested(self, tmp_path):
        root = make_node("a/", 0)
        b = make_node("b/", 1)
        c = make_node("c/", 2)
        leaf = make_node("leaf.txt", 3)
        root.add_child(b)
        b.add_child(c)
        c.add_child(leaf)
        FilesystemBuilder(tmp_path).build(root)
        assert (tmp_path / "a" / "b" / "c" / "leaf.txt").is_file()


class TestFilesystemBuilderSkipRoot:
    """Tests for the skip_root functionality."""

    def test_skip_root_omits_root_dir(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path).build(root, skip_root=True)
        assert not (tmp_path / "project").exists()

    def test_skip_root_places_children_in_base(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path).build(root, skip_root=True)
        assert (tmp_path / "README.md").is_file()
        assert (tmp_path / "src").is_dir()
        assert (tmp_path / "src" / "main.py").is_file()


class TestFilesystemBuilderDryRun:
    """Tests for dry_run mode."""

    def test_dry_run_creates_nothing(self, tmp_path):
        root = simple_tree(tmp_path)
        FilesystemBuilder(tmp_path, dry_run=True).build(root)
        assert not (tmp_path / "project").exists()

    def test_dry_run_returns_correct_counts(self, tmp_path):
        root = simple_tree(tmp_path)
        dirs, files = FilesystemBuilder(tmp_path, dry_run=True).build(root)
        assert dirs == 2
        assert files == 2

    def test_dry_run_summary_flag(self, tmp_path):
        root = make_node("project/", 0)
        builder = FilesystemBuilder(tmp_path, dry_run=True)
        builder.build(root)
        summary = builder.get_summary()
        assert summary["dry_run"] is True


class TestFilesystemBuilderFileContent:
    """Tests for file content writing."""

    def test_empty_comment_creates_empty_file(self, tmp_path):
        root = make_node("project/", 0)
        f = make_node("empty.py", 1)
        root.add_child(f)
        FilesystemBuilder(tmp_path).build(root)
        content = (tmp_path / "project" / "empty.py").read_text()
        assert content == ""

    def test_txt_format_adds_hash_prefix(self, tmp_path):
        root = make_node("project/", 0)
        f = Node(data=FileItem(filename="app.py", level=1, comment="main app"))
        root.add_child(f)
        FilesystemBuilder(tmp_path, input_type="txt").build(root)
        content = (tmp_path / "project" / "app.py").read_text()
        assert content == "# main app"

    def test_json_format_writes_raw_content(self, tmp_path):
        root = make_node("project/", 0)
        f = Node(data=FileItem(filename="config.py", level=1, comment="raw content"))
        root.add_child(f)
        FilesystemBuilder(tmp_path, input_type="json").build(root)
        content = (tmp_path / "project" / "config.py").read_text()
        assert content == "raw content"

    def test_txt_multiline_comment_all_lines_prefixed(self, tmp_path):
        root = make_node("project/", 0)
        f = Node(data=FileItem(filename="notes.py", level=1, comment="line one\nline two"))
        root.add_child(f)
        FilesystemBuilder(tmp_path, input_type="txt").build(root)
        content = (tmp_path / "project" / "notes.py").read_text()
        assert "# line one" in content
        assert "# line two" in content

    def test_format_content_empty_returns_empty(self, tmp_path):
        builder = FilesystemBuilder(tmp_path, input_type="txt")
        assert builder._format_content("") == ""

    def test_format_content_txt_single_line(self, tmp_path):
        builder = FilesystemBuilder(tmp_path, input_type="txt")
        assert builder._format_content("hello") == "# hello"

    def test_format_content_json_passthrough(self, tmp_path):
        builder = FilesystemBuilder(tmp_path, input_type="json")
        assert builder._format_content("raw") == "raw"


class TestFilesystemBuilderSummary:
    """Tests for summary / counter mechanics."""

    def test_summary_keys_present(self, tmp_path):
        root = make_node("project/", 0)
        builder = FilesystemBuilder(tmp_path)
        builder.build(root)
        summary = builder.get_summary()
        assert "directories" in summary
        assert "files" in summary
        assert "total" in summary
        assert "dry_run" in summary

    def test_counters_reset_on_rebuild(self, tmp_path):
        """Calling build() twice should reset counters."""
        root = make_node("project/", 0)
        builder = FilesystemBuilder(tmp_path)
        builder.build(root)
        builder.build(root)  # second call
        summary = builder.get_summary()
        # Should still be 1 dir, 0 files (not doubled)
        assert summary["directories"] == 1
        assert summary["files"] == 0

    def test_total_equals_dirs_plus_files(self, tmp_path):
        root = simple_tree(tmp_path)
        builder = FilesystemBuilder(tmp_path)
        builder.build(root)
        s = builder.get_summary()
        assert s["total"] == s["directories"] + s["files"]

    def test_print_summary_dry_run(self, tmp_path, capsys):
        root = make_node("project/", 0)
        builder = FilesystemBuilder(tmp_path, dry_run=True)
        builder.build(root)
        builder.print_summary()
        output = capsys.readouterr().out
        assert "DRY RUN" in output

    def test_print_summary_live(self, tmp_path, capsys):
        root = make_node("project/", 0)
        builder = FilesystemBuilder(tmp_path)
        builder.build(root)
        builder.print_summary()
        output = capsys.readouterr().out
        assert "Directories" in output
        assert "Files" in output
