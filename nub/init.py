"""
init.py
Set up the .vcs folder structure inside the project root.
"""
import json
import os
import ctypes
from pathlib import Path
from .utils import register_world

DEFAULT_BRANCH = "main"

def _hide_folder(path: Path):
    """Set the 'hidden' attribute on Windows."""
    if os.name == 'nt':
        # 0x02 is the constant for 'Hidden' in Windows
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x02)
        except:
            pass # Fallback for non-Windows or permission issues

def find_vcs_root(start: Path = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".vcs").is_dir():
            return current
        parent = current.parent
        if parent == current:
            raise RuntimeError("Not inside a nub repository. Run 'nub start' first.")
        current = parent

def vcs_dir(project_root: Path) -> Path:
    return project_root / ".vcs"

def objects_dir(project_root: Path) -> Path:
    return project_root / ".vcs" / "objects"

def refs_dir(project_root: Path) -> Path:
    return project_root / ".vcs" / "refs"

def init_repo(project_root: Path) -> str:
    dot_vcs = project_root / ".vcs"
    if dot_vcs.exists():
        register_world(project_root)
        raise FileExistsError(f"Repository already initialised at {dot_vcs}")
    
    (dot_vcs / "objects").mkdir(parents=True)
    (dot_vcs / "refs").mkdir(parents=True)
    (dot_vcs / "HEAD").write_text(f"ref: {DEFAULT_BRANCH}\n")
    (dot_vcs / "config.json").write_text(
        json.dumps({"name": "", "email": "", "user_hash": ""}, indent=2) + "\n"
    )
    
    # Hide the folder from view
    _hide_folder(dot_vcs)
    
    # Register the newly created repository
    register_world(project_root)
    
    return (
        f"Initialised empty NUB repository in {dot_vcs}\n"
        f"  Default flow: {DEFAULT_BRANCH}\n"
        f"  Run 'nub auth --name \"Your Name\" --email you@example.com' to get started."
    )
