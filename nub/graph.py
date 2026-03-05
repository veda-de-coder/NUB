"""
graph.py
A vertical ASCII commit graph generator with TUI layout support.
"""
from pathlib import Path
from .commit import commit_history
from .refs import resolve_head, current_branch
from .utils import short_hash

def get_graph_nodes(vd: Path, od: Path) -> list:
    """Returns a list of commit metadata for graphing."""
    head = resolve_head(vd)
    if not head:
        return []
    return commit_history(od, head)

def print_ascii_graph(vd: Path, od: Path):
    """Fallback ASCII graph."""
    history = get_graph_nodes(vd, od)
    if not history:
        print(" (No history yet) ")
        return
    for i, c in enumerate(history):
        char = "*" if i == 0 else "|"
        print(f" {char} [{short_hash(c['hash'])}] {c['message'][:40]}")
