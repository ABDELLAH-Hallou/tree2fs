# tree2fs

Convert tree-formatted text into filesystem structures.

## Installation
```bash
pip install tree2fs
```

## Quick Start

### Command Line Usage
```bash
# Create structure from tree file
tree2fs tree.txt

# Preview without creating (dry run)
tree2fs tree.txt --dry-run -v

# Create in specific directory
tree2fs tree.txt --base-dir /path/to/project

# Include root directory in creation
tree2fs tree.txt --no-skip-root

# NEW: JSON format with name: content pairs
tree2fs input.json --format json
```

### Python API Usage
```python
from tree2fs import create_from_tree

# Simple usage
stats = create_from_tree("tree.txt", verbose=True)
print(f"Created {stats['total']} items")

# Advanced usage
from tree2fs import TreeParser, FilesystemBuilder
from pathlib import Path

# Parse tree file
parser = TreeParser()
root, _ = parser.build_tree(Path("tree.txt"))

# Build filesystem
builder = FilesystemBuilder(Path("."), verbose=True)
builder.build(root)
builder.print_summary()
```

## Tree File Format
```
project/
├── README.md
├── LICENSE
├── src/
│   ├── __init__.py
│   ├── main.py          # Main module
│   └── utils.py         # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── docs/
    └── index.md
```

## *NEW* JSON Format

Uses name: content pairs to represent the tree structure.

```json
{
  "project": {
    "README.md": "# Project\n\nThis is a project.",
    "LICENSE": "MIT License",
    "src": {
      "__init__.py": "",
      "main.py": "# Main module\n\nimport os\n\ndef main():\n    print('it works!')\n\nmain()"
    },
    "tests": {
      "__init__.py": "",
      "test_main.py": "# Test module\n\nimport os\n\ndef test():\n    assert True\n\ntest()"
    },
    "docs": {
      "index.md": "# Documentation\n\nThis is the documentation."
    }
  }
}

- Directories end with `/`
- Comments start with `#`
- Supports standard tree drawing characters: `│`, `├`, `└`, `─`

## Features

- ✅ Parse tree-formatted text files
- ✅ Create directories and files
- ✅ Dry-run mode for preview
- ✅ Verbose output with comments
- ✅ Skip root directory option
- ✅ Python 3.9+ support
- ✅ Type hints throughout

## Development
```bash
# Clone repository
git clone https://github.com/ABDELLAH-Hallou/tree2fs.git
cd tree2fs

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black tree2fs tests

# Type checking
mypy tree2fs
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.


### 17. `LICENSE`
```
MIT License

Copyright (c) 2025-present Abdellah HALLOU

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```