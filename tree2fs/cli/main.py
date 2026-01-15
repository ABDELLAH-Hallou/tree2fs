"""Command-line interface for tree2fs."""

import sys
import argparse
from pathlib import Path

from tree2fs.parser.json_parser import JsonParser
from ..parser import TreeParser
from ..builder import FilesystemBuilder
from ..exceptions import TreeParseError, FilesystemBuildError
from ..__version__ import __version__


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='tree2fs',
        description='Convert tree-formatted text into filesystem structures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tree2fs tree.txt                    # Create structure from tree.txt
  tree2fs tree.txt --dry-run -v       # Preview what would be created
  tree2fs tree.txt --base-dir /tmp    # Create in /tmp directory
  tree2fs tree.txt --no-skip-root     # Include root directory

Tree file format:
  project/
  ├── README.md
  ├── src/
  │   ├── main.py
  │   └── utils.py
  └── tests/
      └── test_main.py
        """
    )
    
    parser.add_argument(
        'tree_file',
        type=str,
        help='Path to tree file'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['txt', 'json'],
        default='txt',
        help='Input file format (default: txt)'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory to create structure in (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed information'
    )
    parser.add_argument(
        '--no-skip-root',
        action='store_true',
        help='Do not skip the root folder even if already in it'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    tree_file_path = Path(args.tree_file) # Define this early

    try:
        if args.format == 'json':
            # Now tree_file_path is safe to use here
            json_parser = JsonParser()
            root, root_name = json_parser.build_tree(tree_file_path)
        else:
            if args.verbose:
                print(f"📖 Parsing tree file: {tree_file_path}")
            parser = TreeParser()
            root, root_name = parser.build_tree(tree_file_path)
        if args.base_dir in [".", ""]:
            base_path = Path.cwd()
        else:
            base_path = Path(args.base_dir)
        # Determine if we should skip root
        should_skip_root = False
        if not args.no_skip_root and root_name and base_path.name == root_name:
            should_skip_root = True
            if args.verbose:
                print(f"⏭️  Skipping root folder '{root_name}' (already in it)")
        
        # Build filesystem
        if args.verbose:
            print(f"🏗️  Building structure in: {base_path.absolute()}\n")
        
        builder = FilesystemBuilder(
            base_path,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        builder.build(root, skip_root=should_skip_root)
        builder.print_summary()
        
        if not args.dry_run:
            print("\n✅ Structure created successfully!")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except (TreeParseError, FilesystemBuildError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())