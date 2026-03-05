"""
utils.py
SHA-1 hash helper and Global Universe Registry.
"""
import hashlib
import os
import json
from pathlib import Path

def sha1_hash(data: bytes) -> str:
    """Return the SHA-1 hex digest of raw bytes."""
    return hashlib.sha1(data).hexdigest()

def sha1_of_string(text: str) -> str:
    """Convenience wrapper: hash a plain string (UTF-8 encoded)."""
    return sha1_hash(text.encode("utf-8"))

def short_hash(full_hash: str, length: int = 7) -> str:
    """Return a shortened version of a hash for display purposes."""
    return full_hash[:length]

def get_universe_path() -> Path:
    """Returns the path to the global NUB registry."""
    return Path.home() / ".nub_universe"

def register_world(project_path: Path):
    """Add a project path to the global registry."""
    universe_path = get_universe_path()
    worlds = []
    if universe_path.exists():
        try:
            worlds = json.loads(universe_path.read_text())
        except:
            worlds = []
    
    abs_path = str(project_path.resolve())
    if abs_path not in worlds:
        worlds.append(abs_path)
        universe_path.write_text(json.dumps(worlds, indent=2))

def get_all_worlds() -> list:
    """Return all known project paths."""
    universe_path = get_universe_path()
    if not universe_path.exists():
        return []
    try:
        return json.loads(universe_path.read_text())
    except:
        return []

def clean_universe() -> int:
    """Remove paths that no longer exist on disk. Returns count of removed paths."""
    worlds = get_all_worlds()
    existing = [w for l in worlds if (w := Path(l)) and w.exists()]
    removed = len(worlds) - len(existing)
    if removed > 0:
        get_universe_path().write_text(json.dumps([str(p) for p in existing], indent=2))
    return removed
