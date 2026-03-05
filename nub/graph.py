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

def draw_side_panel(stdscr, history, start_y, start_x, width, height):
    """Draws a thin vertical node graph in a specific screen region."""
    if not history:
        stdscr.addstr(start_y, start_x, " (No Snaps) ")
        return

    for i, commit in enumerate(history):
        if i >= height: break
        y = start_y + i
        
        # Draw node
        char = "●" if i == 0 else "○"
        h = short_hash(commit["hash"], 4)
        
        # Layout: [Node] [Hash]
        try:
            stdscr.addstr(y, start_x, f" {char} {h} ", 0)
            if i < len(history) - 1 and (y + 1) < (start_y + height):
                stdscr.addstr(y + 1, start_x + 1, "│", 0)
        except:
            break

def print_ascii_graph(vd: Path, od: Path):
    """Fallback ASCII graph."""
    history = get_graph_nodes(vd, od)
    if not history:
        print(" (No history yet) ")
        return
    for i, c in enumerate(history):
        char = "*" if i == 0 else "|"
        print(f" {char} [{short_hash(c['hash'])}] {c['message'][:40]}")
