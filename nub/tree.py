"""
tree.py
Snapshot an entire project folder into a single tree hash and restore it.
"""
import os
import stat
from pathlib import Path
from .objects import save_blob, load_blob

ALWAYS_IGNORE = {".vcs", "__pycache__", ".DS_Store", ".nubblind"}

def get_blind_list(root: Path):
    """Read .nubblind and return a set of patterns to ignore."""
    blind_file = root / ".nubblind"
    if not blind_file.exists():
        return set()
    patterns = set()
    for line in blind_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.add(line)
    return patterns

def _collect_files(root: Path):
    entries = []
    blind_patterns = get_blind_list(root)
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories in-place
        dirnames[:] = [d for d in sorted(dirnames) 
                       if d not in ALWAYS_IGNORE and d not in blind_patterns]
        
        for fname in sorted(filenames):
            if fname in ALWAYS_IGNORE or fname in blind_patterns:
                continue
            
            abs_path = Path(dirpath) / fname
            rel_path = abs_path.relative_to(root).as_posix()
            
            # Additional check for path-based ignores (e.g. "logs/temp.txt")
            if any(p in rel_path.split("/") for p in blind_patterns):
                continue

            mode = abs_path.stat().st_mode
            is_exec = bool(mode & stat.S_IXUSR)
            entries.append((rel_path, abs_path, is_exec))
    return entries

def _encode_tree(file_entries) -> bytes:
    lines = []
    for rel_path, blob_hash, is_exec in file_entries:
        mode = "exec" if is_exec else "file"
        lines.append(f"{mode} {rel_path} {blob_hash}")
    return "\n".join(lines).encode("utf-8")

def _decode_tree(raw: bytes):
    entries = []
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        mode, rel_path, blob_hash = line.split(" ", 2)
        entries.append((mode, rel_path, blob_hash))
    return entries

def snapshot(project_root: Path, objects_dir: Path) -> str:
    """Walk project_root, store every file as a blob, store the tree."""
    file_entries_for_tree = []
    for rel_path, abs_path, is_exec in _collect_files(project_root):
        data = abs_path.read_bytes()
        blob_hash = save_blob(objects_dir, data)
        file_entries_for_tree.append((rel_path, blob_hash, is_exec))
    tree_bytes = _encode_tree(file_entries_for_tree)
    return save_blob(objects_dir, tree_bytes)

def restore(tree_hash: str, objects_dir: Path, target_root: Path) -> None:
    """Reconstruct the project captured under tree_hash."""
    tree_raw = load_blob(objects_dir, tree_hash)
    for mode, rel_path, blob_hash in _decode_tree(tree_raw):
        dest = target_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(load_blob(objects_dir, blob_hash))
        if mode == "exec":
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def list_tree(tree_hash: str, objects_dir: Path):
    return _decode_tree(load_blob(objects_dir, tree_hash))
