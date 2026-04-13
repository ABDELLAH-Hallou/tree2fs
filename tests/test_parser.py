"""Tests for tree parser."""

import pytest
from pathlib import Path
from tree2fs.parser import TreeParser
from tree2fs.models import FileItem
from tree2fs.exceptions import TreeParseError


def test_parse_line_basic():
    """Test parsing a basic line."""
    parser = TreeParser()
    file_item = parser.parse_line("├── README.md", 1)

    assert file_item is not None
    assert file_item.filename == "README.md"
    assert file_item.level == 1
    assert not file_item.is_directory


def test_parse_line_with_comment():
    """Test parsing a line with comment."""
    parser = TreeParser()
    file_item = parser.parse_line("│   ├── config.py # configuration file", 1)

    assert file_item is not None
    assert file_item.filename == "config.py"
    assert file_item.comment == "configuration file"
    assert file_item.level == 2


def test_parse_line_directory():
    """Test parsing a directory line."""
    parser = TreeParser()
    file_item = parser.parse_line("├── docs/", 1)

    assert file_item is not None
    assert file_item.is_directory
    assert file_item.name == "docs"


def test_parse_line_empty():
    """Test parsing an empty line."""
    parser = TreeParser()
    file_item = parser.parse_line("", 1)

    assert file_item is None


def test_build_tree_simple(tmp_path):
    """Test building a simple tree."""
    tree_content = """project/
├── README.md
├── src/
│   └── main.py
└── tests/
    └── test_main.py
"""

    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(tree_content, encoding="utf-8")

    parser = TreeParser()
    root, _ = parser.build_tree(tree_file)

    assert root.data.name == "project"
    assert len(root.children) == 3  # README.md, src/, tests/

    # Check src directory
    src = root.children[1]
    assert src.data.name == "src"
    assert src.data.is_directory
    assert len(src.children) == 1
    assert src.children[0].data.name == "main.py"


def test_build_tree_empty_file(tmp_path):
    """Test building tree from empty file."""
    tree_file = tmp_path / "empty.txt"
    tree_file.write_text("")

    parser = TreeParser()

    with pytest.raises(TreeParseError, match="empty"):
        parser.build_tree(tree_file)


def test_build_tree_nonexistent_file():
    """Test building tree from nonexistent file."""
    parser = TreeParser()

    with pytest.raises(FileNotFoundError):
        parser.build_tree(Path("nonexistent.txt"))


def test_parse_line_custom_symbol_length():
    """Test parsing with custom symbol length."""
    parser = TreeParser(symbol_length=2)
    file_item = parser.parse_line("│ ├─ file.py", 2)

    assert file_item is not None
    assert file_item.level == 2
