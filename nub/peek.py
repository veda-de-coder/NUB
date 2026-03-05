"""
peek.py
Handles the NUB peek command for viewing file contents.
"""
import sys
from pathlib import Path
from .init import find_vcs_root

def run_peek(args, SYM_ERR, SYM_WARN, red, yellow, blue, _draw_frame):
    """Peek at a file or directory."""
    try:
        root = find_vcs_root()
        target = root / args.file
    except RuntimeError:
        target = Path(args.file)
        
    if not target.exists():
        print(red(f"{SYM_ERR} File not found: {args.file}")); sys.exit(1)
    
    if target.is_dir():
        print(yellow(f"{SYM_WARN} '{args.file}' is a directory. Listing contents:"))
        for item in sorted(target.iterdir()):
            print(f"  {'/' if item.is_dir() else ' '} {item.name}")
        return

    try:
        content = target.read_text().splitlines()
        _draw_frame(f"PEEK: {args.file}", content, blue)
    except Exception as e:
        print(red(f"{SYM_ERR} Could not read file: {e}")); sys.exit(1)
