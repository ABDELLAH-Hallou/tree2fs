"""Integration tests: parse → build pipeline."""

import json
import pytest
from pathlib import Path

from tree2fs.parser import TreeParser
from tree2fs.parser.json_parser import JSONParser
from tree2fs.builder import FilesystemBuilder


class TestTreeParseThenBuild:
    """End-to-end: .txt tree → filesystem."""

    def test_simple_project_created(self, tmp_path):
        tree_content = (
            "project/\n"
            "├── README.md # readme\n"
            "├── src/\n"
            "│   └── main.py # entry\n"
            "└── tests/\n"
            "    └── test_main.py\n"
        )
        tree_file = tmp_path / "tree.txt"
        tree_file.write_text(tree_content, encoding="utf-8")

        root, root_name = TreeParser().build_tree(tree_file)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        FilesystemBuilder(out_dir).build(root)

        assert (out_dir / "project").is_dir()
        assert (out_dir / "project" / "README.md").is_file()
        assert (out_dir / "project" / "src").is_dir()
        assert (out_dir / "project" / "src" / "main.py").is_file()
        assert (out_dir / "project" / "tests" / "test_main.py").is_file()

    def test_comment_written_as_hash_comment(self, tmp_path):
        tree_content = "project/\n└── app.py # main app\n"
        tree_file = tmp_path / "tree.txt"
        tree_file.write_text(tree_content, encoding="utf-8")

        root, _ = TreeParser().build_tree(tree_file)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        FilesystemBuilder(out_dir, input_type="txt").build(root)

        content = (out_dir / "project" / "app.py").read_text()
        assert content == "# main app"

    def test_skip_root_matches_base_dir(self, tmp_path):
        """When base_dir name matches root_name, skip_root should work."""
        tree_content = "project/\n├── README.md\n└── main.py\n"
        tree_file = tmp_path / "tree.txt"
        tree_file.write_text(tree_content, encoding="utf-8")

        root, root_name = TreeParser().build_tree(tree_file)
        # Simulate already being inside 'project' dir
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        should_skip = project_dir.name == root_name.rstrip("/")
        FilesystemBuilder(project_dir).build(root, skip_root=should_skip)

        # Files should land directly in project_dir
        assert (project_dir / "README.md").is_file()
        assert (project_dir / "main.py").is_file()
        # Root dir itself should not be re-created inside
        assert not (project_dir / "project").exists()

    def test_dry_run_nothing_created(self, tmp_path):
        tree_content = "project/\n├── README.md\n└── src/\n    └── main.py\n"
        tree_file = tmp_path / "tree.txt"
        tree_file.write_text(tree_content, encoding="utf-8")

        root, _ = TreeParser().build_tree(tree_file)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        FilesystemBuilder(out_dir, dry_run=True).build(root)

        assert not (out_dir / "project").exists()


class TestJSONParseThenBuild:
    """End-to-end: .json → filesystem."""

    def test_json_project_created(self, tmp_path):
        data = {
            "myapp": {
                "README.md": "readme content",
                "src": {
                    "main.py": "entry point"
                }
            }
        }
        json_file = tmp_path / "struct.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        root, root_name = JSONParser().build_tree(json_file)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        FilesystemBuilder(out_dir, input_type="json").build(root)

        assert (out_dir / "myapp").is_dir()
        assert (out_dir / "myapp" / "README.md").is_file()
        assert (out_dir / "myapp" / "src").is_dir()
        assert (out_dir / "myapp" / "src" / "main.py").is_file()

    def test_json_file_content_written(self, tmp_path):
        data = {"project": {"notes.txt": "hello from json"}}
        json_file = tmp_path / "s.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        root, _ = JSONParser().build_tree(json_file)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        FilesystemBuilder(out_dir, input_type="json").build(root)

        content = (out_dir / "project" / "notes.txt").read_text()
        assert content == "hello from json"

    def test_fixture_sample_tree_full_pipeline(self, tmp_path):
        fixture = Path(__file__).parent / "fixtures" / "sample_tree.txt"
        root, _ = TreeParser().build_tree(fixture)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        dirs, files = FilesystemBuilder(out_dir).build(root)
        assert dirs >= 4   # project, src, tests, docs
        assert files >= 6  # README, LICENSE, pyproject, __init__ × 2, etc.
        assert (out_dir / "project" / "src" / "main.py").is_file()
        assert (out_dir / "project" / "docs" / "index.md").is_file()
