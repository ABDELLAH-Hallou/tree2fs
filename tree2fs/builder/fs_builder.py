"""Build filesystem structure from tree data structure."""

import warnings
from pathlib import Path
from typing import Set, Tuple
from ..models.node import Node
from ..exceptions import FilesystemBuildError

class FilesystemBuilder:
    """Creates filesystem structure from a tree data structure.
    
    This class traverses a Node structure and creates the corresponding
    files and directories on the filesystem.
    """
    
    def __init__(self, base_dir: Path, dry_run: bool = False, verbose: bool = False):
        """Initialize the filesystem builder.
        
        Args:
            base_dir: Base directory to create structure in
            dry_run: If True, don't actually create files/directories
            verbose: If True, print detailed information
        """
        self.base_dir = Path(base_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.created_dirs: Set[str] = set()
        self.created_files: Set[str] = set()
    
    def _create_directory(self, path: Path, node: Node) -> None:
        """Create a directory.
        
        Args:
            path: Full path to create
            node: Node containing metadata
        """
        try:
            if not self.dry_run:
                path.mkdir(parents=True, exist_ok=True)
            
            self.created_dirs.add(str(path))
            
            if self.verbose:
                action = "[DRY RUN] Would create" if self.dry_run else "Created"
                print(f"{action} directory: {path}")
                if node.data.comment:
                    print(f"  → Comment: {node.data.comment}")
        
        except OSError as e:
            raise FilesystemBuildError(f"Failed to create directory {path}: {e}")
    
    def _create_file(self, path: Path, node: Node) -> None:
        """Create a file with content from node.data.comment."""
        try:
            if not self.dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                # MODIFIED: Instead of path.touch(), we write the content
                with open(path, 'w', encoding='utf-8') as f:
                    if node.data.comment:
                        f.write(node.data.comment)
            
            self.created_files.add(str(path))
            
            if self.verbose:
                action = "[DRY RUN] Would create" if self.dry_run else "Created"
                print(f"{action} file: {path}")
                if node.data.comment:
                    # Show a preview of content in verbose mode
                    preview = (node.data.comment[:30] + '..') if len(node.data.comment) > 30 else node.data.comment
                    print(f"   → Content: {preview}")
        
        except OSError as e:
            raise FilesystemBuildError(f"Failed to create file {path}: {e}")
    
    def _traverse_and_create(self, node: Node, skip_root: bool = False) -> None:
        """Recursively traverse tree and create filesystem structure.
        
        This uses pre-order traversal: process current node, then children.
        
        Args:
            node: Current node to process
            skip_root: If True, skip creating the root directory itself
        """
        # Get full path for current node
        full_path = node.get_full_path()
        if skip_root:
            full_path = Path(*full_path.parts[1:])
        
        # Create current node unless we're skipping it
        if node.data.is_directory:
            self._create_directory(self.base_dir / full_path, node)
        else:
            self._create_file(self.base_dir / full_path, node)
        
        # Recursively process all children
        for child in node.children:
            self._traverse_and_create(child, skip_root=skip_root)
    
    def build(self, root: Node, skip_root: bool = False) -> Tuple[int, int]:
        """Build the filesystem structure from tree.
        
        Args:
            root: Root node of the tree
            skip_root: If True, skip creating the root directory itself
            
        Returns:
            Tuple of (num_directories, num_files) created
        """
        # Reset counters
        self.created_dirs.clear()
        self.created_files.clear()
        
        # Start traversal
        self._traverse_and_create(root, skip_root=skip_root)
        
        return len(self.created_dirs), len(self.created_files)
    
    def get_summary(self) -> dict:
        """Get summary of created files and directories.
        
        Returns:
            Dictionary with creation statistics
        """
        return {
            'directories': len(self.created_dirs),
            'files': len(self.created_files),
            'total': len(self.created_dirs) + len(self.created_files),
            'dry_run': self.dry_run
        }
    
    def print_summary(self) -> None:
        """Print summary of created files and directories."""
        summary = self.get_summary()
        prefix = "[DRY RUN] " if summary['dry_run'] else ""
        
        print(f"\n{prefix}Summary:")
        print(f"  📁 Directories: {summary['directories']}")
        print(f"  📄 Files: {summary['files']}")
        print(f"  📊 Total: {summary['total']}")
        
        if summary['dry_run']:
            print("\n💡 Run without --dry-run to actually create the structure.")