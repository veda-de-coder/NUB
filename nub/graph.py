"""
graph.py
A vertical ASCII commit graph generator.
Shows the flow of commits as nodes and lines.
"""
from pathlib import Path
from .commit import commit_history
from .refs import resolve_head, current_branch
from .utils import short_hash

def generate_graph(vd: Path, od: Path) -> list:
    """
    Generate a list of strings representing the commit graph.
    Format: * [short_hash] (branch) Message
    """
    head = resolve_head(vd)
    if not head:
        return [" (no history) "]
    
    history = commit_history(od, head)
    branch_name = current_branch(vd) or "(detached)"
    
    lines = []
    for i, commit in enumerate(history):
        h = short_hash(commit["hash"])
        msg = commit["message"].split('\n')[0][:50]
        author = commit.get("author", "unknown")
        
        # Simple vertical line representation
        prefix = "* " if i == 0 else "| "
        color_branch = f"({branch_name})" if i == 0 else ""
        
        line = f"{prefix} {h} {color_branch} {msg} [{author}]"
        lines.append(line)
        
        if i < len(history) - 1:
            lines.append("|")
            
    return lines

def print_ascii_graph(vd: Path, od: Path):
    """Fallback ASCII graph for regular terminal."""
    graph_lines = generate_graph(vd, od)
    for line in graph_lines:
        print(line)
