"""Extended tests for TreeParser."""

import warnings
import pytest
from pathlib import Path

from tree2fs.parser import TreeParser
from tree2fs.exceptions import TreeParseError


class TestTreeParserParseLine:
    """Unit tests for TreeParser.parse_line."""

    def setup_method(self):
        self.parser = TreeParser()

    # --- Happy path ---

    def test_root_level_file(self):
        item = self.parser.parse_line("main.py", 1)
        assert item is not None
        assert item.filename == "main.py"
        assert item.level == 0

    def test_root_level_directory(self):
        item = self.parser.parse_line("project/", 1)
        assert item is not None
        assert item.filename == "project/"
        assert item.level == 0
        assert item.is_directory

    def test_first_level_branch(self):
        item = self.parser.parse_line("├── README.md", 1)
        assert item.filename == "README.md"
        assert item.level == 1

    def test_first_level_last_child(self):
        item = self.parser.parse_line("└── setup.py", 1)
        assert item.filename == "setup.py"
        assert item.level == 1

    def test_second_level_nested(self):
        item = self.parser.parse_line("│   ├── config.py", 1)
        assert item.filename == "config.py"
        assert item.level == 2

    def test_deep_nesting_level_3(self):
        item = self.parser.parse_line("│   │   └── deep.py", 1)
        assert item.filename == "deep.py"
        assert item.level == 3

    # --- Comments ---

    def test_comment_stripped(self):
        item = self.parser.parse_line("├── main.py # entry point", 1)
        assert item.comment == "entry point"

    def test_comment_with_extra_spaces(self):
        item = self.parser.parse_line("├── app.py   #   launch app  ", 1)
        assert item.comment == "launch app"

    def test_no_comment_gives_empty_string(self):
        item = self.parser.parse_line("├── main.py", 1)
        assert item.comment == ""

    def test_hash_in_comment_preserved(self):
        item = self.parser.parse_line("├── file.py # uses #hash", 1)
        assert item.comment == "uses #hash"

    # --- Empty / whitespace lines ---

    def test_empty_line_returns_none(self):
        assert self.parser.parse_line("", 1) is None

    def test_whitespace_only_line_returns_none(self):
        assert self.parser.parse_line("   \t  ", 1) is None

    def test_newline_only_returns_none(self):
        assert self.parser.parse_line("\n", 1) is None

    # --- Line with only tree characters ---

    def test_tree_chars_only_warns_and_returns_none(self):
        with pytest.warns(SyntaxWarning):
            result = self.parser.parse_line("│   ├──", 5)
        assert result is None

    # --- Inconsistent indentation ---

    def test_inconsistent_indentation_warns(self):
        with pytest.warns(SyntaxWarning, match="Inconsistent indentation"):
            self.parser.parse_line("│ file.py", 1)  # 2 chars indent, not multiple of 4

    # --- Custom symbol length ---

    def test_custom_symbol_length_2(self):
        parser2 = TreeParser(symbol_length=2)
        item = parser2.parse_line("│ file.py", 1)
        assert item is not None
        assert item.level == 1

    def test_custom_symbol_length_level_2(self):
        parser2 = TreeParser(symbol_length=2)
        item = parser2.parse_line("│ │ nested.py", 1)
        assert item.level == 2

    # --- line_number populated ---

    def test_line_number_stored(self):
        item = self.parser.parse_line("├── x.py", 42)
        assert item.line_number == 42


class TestTreeParserBuildTree:
    """Tests for TreeParser.build_tree."""

    def setup_method(self):
        self.parser = TreeParser()

    def _write(self, tmp_path, content, name="tree.txt"):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    # --- Errors ---

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            self.parser.build_tree(tmp_path / "nope.txt")

    def test_empty_file_raises(self, tmp_path):
        p = self._write(tmp_path, "")
        with pytest.raises(TreeParseError, match="empty"):
            self.parser.build_tree(p)

    def test_only_blank_lines_raises(self, tmp_path):
        p = self._write(tmp_path, "\n\n\n")
        with pytest.raises(TreeParseError, match="No valid nodes"):
            self.parser.build_tree(p)

    def test_level_skip_raises(self, tmp_path):
        # Jump from level 0 directly to level 2 (no level 1 parent)
        content = "project/\n│   │   └── orphan.py\n"
        p = self._write(tmp_path, content)
        with pytest.raises(TreeParseError, match="no parent"):
            self.parser.build_tree(p)

    # --- Root ---

    def test_root_single_file(self, tmp_path):
        p = self._write(tmp_path, "project/\n")
        root, root_name = self.parser.build_tree(p)
        assert root.data.name == "project"
        # root_name_to_skip is stored as file_item.name (trailing slash stripped)
        assert root_name == "project"
        assert root.children == []

    def test_root_name_to_skip_returned(self, tmp_path):
        p = self._write(tmp_path, "myapp/\n├── main.py\n")
        _, root_name = self.parser.build_tree(p)
        # root_name_to_skip is stored as file_item.name (trailing slash stripped)
        assert root_name == "myapp"

    # --- Children ---

    def test_flat_children(self, tmp_path):
        content = "project/\n├── README.md\n├── setup.py\n└── main.py\n"
        p = self._write(tmp_path, content)
        root, _ = self.parser.build_tree(p)
        assert len(root.children) == 3
        names = [c.data.name for c in root.children]
        assert names == ["README.md", "setup.py", "main.py"]

    def test_nested_children(self, tmp_path):
        content = (
            "project/\n"
            "├── README.md\n"
            "├── src/\n"
            "│   └── main.py\n"
            "└── tests/\n"
            "    └── test_main.py\n"
        )
        p = self._write(tmp_path, content)
        root, _ = self.parser.build_tree(p)
        assert len(root.children) == 3
        src = root.children[1]
        assert src.data.name == "src"
        assert len(src.children) == 1
        assert src.children[0].data.name == "main.py"

    def test_deeply_nested(self, tmp_path):
        content = (
            "root/\n"
            "└── a/\n"
            "    └── b/\n"
            "        └── leaf.txt\n"
        )
        p = self._write(tmp_path, content)
        root, _ = self.parser.build_tree(p)
        a = root.children[0]
        b = a.children[0]
        leaf = b.children[0]
        assert leaf.data.name == "leaf.txt"
        assert leaf.depth == 3

    def test_comments_preserved(self, tmp_path):
        content = (
            "project/\n"
            "├── main.py # entry point\n"
            "└── utils.py # helpers\n"
        )
        p = self._write(tmp_path, content)
        root, _ = self.parser.build_tree(p)
        assert root.children[0].data.comment == "entry point"
        assert root.children[1].data.comment == "helpers"

    def test_blank_lines_ignored(self, tmp_path):
        content = "project/\n\n├── README.md\n\n└── main.py\n"
        p = self._write(tmp_path, content)
        root, _ = self.parser.build_tree(p)
        assert len(root.children) == 2

    def test_multiple_root_nodes_warns(self, tmp_path):
        content = "project/\nsecond_root/\n"
        p = self._write(tmp_path, content)
        with pytest.warns(UserWarning, match="Multiple root-level"):
            self.parser.build_tree(p)

    def test_fixture_sample_tree(self):
        """Integration test against the shipped fixture file."""
        fixture = Path(__file__).parent / "fixtures" / "sample_tree.txt"
        root, root_name = self.parser.build_tree(fixture)
        assert root.data.name == "project"
        top_names = [c.data.name for c in root.children]
        assert "README.md" in top_names
        assert "src" in top_names
        assert "tests" in top_names
        assert "docs" in top_names
