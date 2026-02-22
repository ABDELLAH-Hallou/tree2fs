"""Parser for tree file format into tree data structure."""

import warnings
from pathlib import Path
from typing import List, Optional, Tuple
from ..models.file_item import FileItem
from ..models.node import Node
from ..exceptions import TreeParseError

class TreeParser:
    """Parser for converting tree file format into Node structure.
    
    This parser reads a tree-formatted file (with │, ├, └, ─ characters)
    and builds a proper tree data structure.
    """
    
    def __init__(self, symbol_length: int = 4):
        """Initialize the parser.
        
        Args:
            symbol_length: Number of characters per indentation level (default: 4)
        """
        self.symbol_length = symbol_length
    
    def parse_line(self, line: str, line_num: int) -> Optional[FileItem]:
        """Parse a single line from the tree file.
        
        Args:
            line: Line to parse
            line_num: Line number (for error reporting)
            
        Returns:
            FileItem if line is valid, None if line should be skipped
            
        Raises:
            TreeParseError: If line format is critically invalid
        """
        line = line.rstrip('\n\r')
        
        # Skip empty lines
        if not line.strip():
            return None
        
        # Parse comment (everything after #)
        components = line.split("#", maxsplit=1)
        comment = components[1].strip() if len(components) > 1 else ""
        file_part = components[0].rstrip()
        
        # Extract filename by stripping tree drawing characters
        filename = file_part.lstrip('│└├─ ')
        
        if not filename:
            warnings.warn(
                f"Invalid line format at line {line_num}: '{line}'",
                SyntaxWarning,
                stacklevel=3
            )
            return None
        
        # Calculate indentation level
        indent_chars = len(file_part) - len(filename)
        if indent_chars % self.symbol_length != 0:
            warnings.warn(
                f"Inconsistent indentation at line {line_num}: "
                f"expected multiple of {self.symbol_length}, got {indent_chars}",
                SyntaxWarning,
                stacklevel=3
            )
        
        level = indent_chars // self.symbol_length
        
        # Create FileItem
        return FileItem(
            filename=filename,
            level=level,
            comment=comment,
            line_number=line_num
        )
    
    def build_tree(self, tree_file: Path) -> Tuple[Node, Optional[str]]:
        """Build a tree structure from a tree file.
        
        This method reads the tree file and constructs a proper tree data structure
        by maintaining a stack of nodes at each level and properly linking parent-child
        relationships.
        
        Args:
            tree_file: Path to the tree file
            
        Returns:
            root Node
            
        Raises:
            FileNotFoundError: If tree file doesn't exist
            TreeParseError: If tree file format is invalid
        """
        if not tree_file.exists():
            raise FileNotFoundError(f"Tree file not found: {tree_file}")
        
        # Read file
        try:
            with open(tree_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            raise TreeParseError(f"Failed to read tree file: {e}")
        
        if not lines:
            raise TreeParseError("Tree file is empty")
        
        # Stack to track nodes at each level
        # level_stack[i] contains the most recent node at level i
        level_stack: List[Optional[Node]] = []
        root: Optional[Node] = None
        root_name_to_skip: Optional[str] = None

        for line_num, line in enumerate(lines, start=1):
            file_item = self.parse_line(line, line_num)
            
            if file_item is None:
                continue
            
            level = file_item.level
            
            # Create node for this item
            node = Node(data=file_item)
            
            # Handle root node (level 0)
            if level == 0:
                if root is None:
                    root = node
                    level_stack = [node]
                    root_name_to_skip = file_item.name 
                else:
                    # Multiple root nodes - treat as siblings under virtual root
                    warnings.warn(
                        f"Multiple root-level nodes found at line {line_num}",
                        UserWarning,
                        stacklevel=2
                    )
                    level_stack[0] = node
            else:
                # Ensure we have a parent
                if level > len(level_stack):
                    raise TreeParseError(
                        f"Line {line_num}: Level {level} has no parent "
                        f"(previous max level was {len(level_stack) - 1})"
                    )
                # Trim stack to current level (remove deeper levels)
                level_stack = level_stack[:level]
                if level > 0 and len(level_stack) >= level:
                    parent = level_stack[level - 1]
                    parent.add_child(node)
                
                # Add current node to stack
                if level == len(level_stack):
                    level_stack.append(node)
                else:
                    level_stack[level] = node
        
        if root is None:
            raise TreeParseError("No valid nodes found in tree file")
        
        return root,root_name_to_skip