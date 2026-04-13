"""Tests for JSONParser."""

import json
import pytest
from pathlib import Path

from tree2fs.parser.json_parser import JSONParser
from tree2fs.exceptions import TreeParseError


class TestJSONParser:
    """Tests for the JSONParser class."""

    def setup_method(self):
        self.parser = JSONParser()

    def _write_json(self, tmp_path, data, name="input.json"):
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    # --- Errors ---

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            self.parser.build_tree(tmp_path / "missing.json")

    def test_malformed_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json}", encoding="utf-8")
        with pytest.raises(TreeParseError, match="Invalid JSON"):
            self.parser.build_tree(p)

    def test_empty_json_object_raises(self, tmp_path):
        p = self._write_json(tmp_path, {})
        with pytest.raises(TreeParseError, match="empty"):
            self.parser.build_tree(p)

    def test_non_dict_root_raises(self, tmp_path):
        p = tmp_path / "list.json"
        p.write_text('["item1", "item2"]', encoding="utf-8")
        with pytest.raises(TreeParseError, match="root must be an object"):
            self.parser.build_tree(p)

    # --- Root node ---

    def test_root_name_returned(self, tmp_path):
        data = {"myproject": {}}
        p = self._write_json(tmp_path, data)
        root, root_name = self.parser.build_tree(p)
        assert root.data.name == "myproject"
        assert root_name == "myproject"

    def test_root_with_no_children(self, tmp_path):
        data = {"empty_project": {}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        assert root.children == []

    # --- Children ---

    def test_flat_file_children(self, tmp_path):
        data = {
            "project": {
                "README.md": "readme content",
                "setup.py": "setup content",
            }
        }
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        assert len(root.children) == 2
        child_names = {c.data.name for c in root.children}
        assert child_names == {"README.md", "setup.py"}

    def test_file_content_stored_in_comment(self, tmp_path):
        data = {"project": {"README.md": "Hello World"}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        readme = root.children[0]
        assert readme.data.comment == "Hello World"

    def test_nested_directories(self, tmp_path):
        data = {
            "project": {
                "src": {
                    "main.py": "entry point"
                },
                "tests": {
                    "test_main.py": "tests here"
                }
            }
        }
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        assert len(root.children) == 2
        child_names = {c.data.name for c in root.children}
        assert child_names == {"src", "tests"}
        # src should have main.py as child
        src = next(c for c in root.children if c.data.name == "src")
        assert len(src.children) == 1
        assert src.children[0].data.name == "main.py"
        assert src.children[0].data.comment == "entry point"

    def test_directory_node_has_empty_comment(self, tmp_path):
        data = {"project": {"src": {"main.py": "code"}}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        src = root.children[0]
        assert src.data.comment == ""

    def test_levels_assigned_correctly(self, tmp_path):
        data = {"root": {"child": {"grandchild": "leaf content"}}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        assert root.data.level == 0
        child = root.children[0]
        assert child.data.level == 1
        grandchild = child.children[0]
        assert grandchild.data.level == 2

    def test_non_string_values_coerced_to_string(self, tmp_path):
        data = {"project": {"count.txt": 42, "flag.txt": True}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        child_comments = {c.data.name: c.data.comment for c in root.children}
        assert child_comments["count.txt"] == "42"
        assert child_comments["flag.txt"] == "True"

    def test_deeply_nested_structure(self, tmp_path):
        data = {"a": {"b": {"c": {"d": "deep"}}}}
        p = self._write_json(tmp_path, data)
        root, _ = self.parser.build_tree(p)
        # Traverse to leaf
        node = root
        for expected_name in ["b", "c", "d"]:
            node = node.children[0]
            assert node.data.name == expected_name
        assert node.data.comment == "deep"
