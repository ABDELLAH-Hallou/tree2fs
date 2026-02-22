import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ..models.file_item import FileItem
from ..models.node import Node
from ..exceptions import TreeParseError

class JsonParser:
    """Parser for converting JSON structures into a Node structure.
    
    This parser reads a JSON file where keys represent filenames/directories
    and values represent file content or nested dictionaries.
    """

    def __init__(self):
        pass

    def _build_recursive(self, data: Union[Dict, str], name: str, level: int) -> Node:
        """Recursively convert dictionary levels into Node/FileItem objects."""
        
        # Create the FileItem for this specific entry
        # Note: JSON format doesn't natively support the '# comment' syntax 
        # unless we explicitly look for a metadata key, so we leave it empty.
        file_item = FileItem(
            filename=name,
            level=level,
            comment="",
            line_number=0  # Not applicable for JSON blobs
        )
        
        node = Node(data=file_item)

        # If the value is a dictionary, it's a directory: process children
        if isinstance(data, dict):
            for child_name, child_content in data.items():
                child_node = self._build_recursive(child_content, child_name, level + 1)
                node.add_child(child_node)
        # If it's a string, it's a file: the string is the content
        # (The actual file writing logic is handled by the Processor, not the Parser)
        
        return node

    def build_tree(self, json_path: Path) -> Tuple[Node, Optional[str]]:
        """Build a tree structure from a JSON file.
        
        Args:
            json_path: Path to the .json file
            
        Returns:
            Tuple of (root Node, root_name_to_skip)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            TreeParseError: If JSON is malformed or empty
        """
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TreeParseError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise TreeParseError(f"Failed to read JSON file: {e}")

        if not data:
            raise TreeParseError("JSON file is empty")

        # In your provided JSON, there is a single top-level key ("project")
        if len(data) != 1:
            # If there are multiple top-level keys, we wrap them or pick the first
            # Following the tree_parser logic, we usually expect one root.
            root_name = list(data.keys())[0]
            root_content = data[root_name]
        else:
            root_name = list(data.keys())[0]
            root_content = data[root_name]

        root_node = self._build_recursive(root_content, root_name, 0)
        
        return root_node, root_name