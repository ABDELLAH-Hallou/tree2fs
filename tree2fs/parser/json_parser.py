import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ..models.file_item import FileItem
from ..models.node import Node
from ..exceptions import TreeParseError

class JSONParser:
    """Parser for converting JSON structures into a Node structure.
    
    This parser maps JSON keys to filenames and JSON values to file content
    (stored in the 'comment' field of FileItem).
    """

    def __init__(self):
        pass

    def _build_recursive(self, data: Any, name: str, level: int) -> Node:
        """Recursively convert JSON keys/values into Node/FileItem objects."""
        
        # If the value is a string, it's file content. 
        # If it's a dict, it's a directory (content is empty).
        is_dir = isinstance(data, dict)
        content = "" if is_dir else str(data)
        
        # Create the FileItem
        # We store the JSON value in 'comment' as requested
        file_item = FileItem(
            filename=name,
            level=level,
            comment=content,
            line_number=0 
        )
        
        node = Node(data=file_item)

        # If it's a directory, traverse its children
        if is_dir:
            for child_name, child_content in data.items():
                child_node = self._build_recursive(child_content, child_name, level + 1)
                node.add_child(child_node)
        
        return node

    def build_tree(self, json_path: Path) -> Tuple[Node, Optional[str]]:
        """Build a tree structure from a JSON file.
        
        Args:
            json_path: Path to the .json file
            
        Returns:
            Tuple of (root Node, root_name_to_skip)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            TreeParseError: If JSON is malformed
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

        # Extract the root key (e.g., "project")
        if not isinstance(data, dict):
            raise TreeParseError("JSON root must be an object")

        root_name = list(data.keys())[0]
        root_content = data[root_name]

        # Build the tree starting from the root key
        root_node = self._build_recursive(root_content, root_name, 0)
        
        return root_node, root_name