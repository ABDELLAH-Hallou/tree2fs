"""Tests for FileItem and Node models."""

import pytest
from pydantic import ValidationError
from pathlib import Path

from tree2fs.models.file_item import FileItem
from tree2fs.models.node import Node


# ---------------------------------------------------------------------------
# FileItem tests
# ---------------------------------------------------------------------------

class TestFileItem:
    """Tests for the FileItem model."""

    # --- Construction ---

    def test_basic_file(self):
        item = FileItem(filename="main.py", level=0)
        assert item.filename == "main.py"
        assert item.level == 0
        assert item.comment == ""
        assert item.line_number == 0

    def test_basic_directory(self):
        item = FileItem(filename="src/", level=1)
        assert item.filename == "src/"
        assert item.is_directory

    def test_file_with_comment_and_line_number(self):
        item = FileItem(filename="config.py", level=2, comment="config module", line_number=5)
        assert item.comment == "config module"
        assert item.line_number == 5

    # --- Validation ---

    def test_empty_filename_raises(self):
        with pytest.raises(ValidationError):
            FileItem(filename="", level=0)

    def test_whitespace_only_filename_raises(self):
        with pytest.raises(ValidationError):
            FileItem(filename="   ", level=0)

    def test_invalid_chars_raises(self):
        for char in ['<', '>', ':', '"', '|', '?', '*']:
            with pytest.raises(ValidationError, match="invalid characters"):
                FileItem(filename=f"bad{char}name.py", level=0)

    def test_negative_level_raises(self):
        with pytest.raises(ValidationError):
            FileItem(filename="file.py", level=-1)

    # --- is_directory property ---

    def test_file_without_dot_is_directory(self):
        # No dot → treated as directory
        item = FileItem(filename="Makefile", level=0)
        assert item.is_directory

    def test_file_with_dot_is_not_directory(self):
        item = FileItem(filename="README.md", level=0)
        assert not item.is_directory

    def test_trailing_slash_is_directory(self):
        item = FileItem(filename="src/", level=0)
        assert item.is_directory

    def test_dotfile_is_directory(self):
        # e.g. ".gitignore" has a dot only as prefix → no extension in filename → still dir?
        # Per impl: '.' not in filename → False, so .gitignore HAS a dot → not directory
        item = FileItem(filename=".gitignore", level=0)
        # .gitignore contains a dot so is_directory returns False
        assert not item.is_directory

    # --- name property ---

    def test_name_strips_trailing_slash(self):
        item = FileItem(filename="docs/", level=0)
        assert item.name == "docs"

    def test_name_no_trailing_slash(self):
        item = FileItem(filename="main.py", level=0)
        assert item.name == "main.py"

    # --- extension property ---

    def test_extension_of_file(self):
        item = FileItem(filename="app.py", level=0)
        assert item.extension == "py"

    def test_extension_of_directory_is_none(self):
        item = FileItem(filename="src/", level=0)
        assert item.extension is None

    def test_extension_multiple_dots(self):
        item = FileItem(filename="archive.tar.gz", level=0)
        assert item.extension == "gz"

    # --- name_without_extension property ---

    def test_name_without_extension_file(self):
        item = FileItem(filename="main.py", level=0)
        assert item.name_without_extension == "main"

    def test_name_without_extension_directory(self):
        item = FileItem(filename="src/", level=0)
        assert item.name_without_extension == "src"

    def test_name_without_extension_no_dot(self):
        item = FileItem(filename="Makefile", level=0)
        assert item.name_without_extension == "Makefile"

    # --- get_indented_display ---

    def test_indented_display_level_0(self):
        item = FileItem(filename="root/", level=0)
        assert item.get_indented_display() == "root/"

    def test_indented_display_level_2(self):
        item = FileItem(filename="file.py", level=2)
        assert item.get_indented_display("  ") == "    file.py"

    def test_indented_display_custom_char(self):
        item = FileItem(filename="x.py", level=3)
        assert item.get_indented_display("\t") == "\t\t\tx.py"

    # --- __str__ ---

    def test_str_returns_name(self):
        item = FileItem(filename="docs/", level=0)
        assert str(item) == "docs"

    # --- frozen model ---

    def test_model_is_frozen(self):
        item = FileItem(filename="file.py", level=0)
        with pytest.raises(ValidationError):
            item.filename = "other.py"


# ---------------------------------------------------------------------------
# Node tests
# ---------------------------------------------------------------------------

class TestNode:
    """Tests for the Node model."""

    def _make_node(self, filename="root/", level=0):
        return Node(data=FileItem(filename=filename, level=level))

    # --- Construction ---

    def test_node_defaults(self):
        node = self._make_node()
        assert node.children == []
        assert node.parent is None

    # --- add_child / parent linking ---

    def test_add_child_sets_parent(self):
        root = self._make_node("root/", 0)
        child = self._make_node("child/", 1)
        root.add_child(child)
        assert child in root.children
        assert child.parent is root

    def test_add_multiple_children(self):
        root = self._make_node("root/", 0)
        for i in range(3):
            root.add_child(self._make_node(f"child{i}.py", 1))
        assert len(root.children) == 3

    # --- remove_child ---

    def test_remove_child_success(self):
        root = self._make_node()
        child = self._make_node("child.py", 1)
        root.add_child(child)
        result = root.remove_child(child)
        assert result is True
        assert child not in root.children
        assert child.parent is None

    def test_remove_nonexistent_child_returns_false(self):
        root = self._make_node()
        stranger = self._make_node("stranger.py", 1)
        assert root.remove_child(stranger) is False

    # --- is_leaf / is_root ---

    def test_leaf_node(self):
        node = self._make_node()
        assert node.is_leaf

    def test_non_leaf_node(self):
        root = self._make_node()
        root.add_child(self._make_node("child.py", 1))
        assert not root.is_leaf

    def test_root_node(self):
        node = self._make_node()
        assert node.is_root

    def test_non_root_node(self):
        root = self._make_node()
        child = self._make_node("child.py", 1)
        root.add_child(child)
        assert not child.is_root

    # --- degree ---

    def test_degree_zero(self):
        node = self._make_node()
        assert node.degree == 0

    def test_degree_multiple(self):
        root = self._make_node()
        root.add_child(self._make_node("a.py", 1))
        root.add_child(self._make_node("b.py", 1))
        assert root.degree == 2

    # --- height ---

    def test_height_leaf(self):
        assert self._make_node().height == 0

    def test_height_one_level(self):
        root = self._make_node()
        root.add_child(self._make_node("child.py", 1))
        assert root.height == 1

    def test_height_nested(self):
        root = self._make_node("root/", 0)
        mid = self._make_node("mid/", 1)
        leaf = self._make_node("leaf.py", 2)
        mid.add_child(leaf)
        root.add_child(mid)
        assert root.height == 2

    # --- depth ---

    def test_depth_root(self):
        assert self._make_node().depth == 0

    def test_depth_child(self):
        root = self._make_node()
        child = self._make_node("child.py", 1)
        root.add_child(child)
        assert child.depth == 1

    def test_depth_grandchild(self):
        root = self._make_node("root/", 0)
        mid = self._make_node("mid/", 1)
        leaf = self._make_node("leaf.py", 2)
        root.add_child(mid)
        mid.add_child(leaf)
        assert leaf.depth == 2

    # --- get_path_components / get_full_path ---

    def test_path_components_root_only(self):
        root = self._make_node("project/", 0)
        assert root.get_path_components() == ["project"]

    def test_path_components_nested(self):
        root = self._make_node("project/", 0)
        src = self._make_node("src/", 1)
        main = self._make_node("main.py", 2)
        root.add_child(src)
        src.add_child(main)
        assert main.get_path_components() == ["project", "src", "main.py"]

    def test_get_full_path(self):
        root = self._make_node("project/", 0)
        src = self._make_node("src/", 1)
        main = self._make_node("main.py", 2)
        root.add_child(src)
        src.add_child(main)
        assert main.get_full_path() == Path("project", "src", "main.py")

    # --- __str__ / __repr__ ---

    def test_str(self):
        node = self._make_node("docs/", 0)
        assert str(node) == "docs"

    def test_repr(self):
        node = self._make_node("file.py", 0)
        r = repr(node)
        assert "file.py" in r
        assert "level=0" in r
        assert "children=0" in r
