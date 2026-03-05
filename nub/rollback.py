"""
rollback.py — Hour 4
Restore any past project snapshot — by step count or by commit hash.

Key design decision (Rule 4):
  The objects/ store is APPEND-ONLY.  Rollback never deletes history.
  It simply moves the branch pointer backward and rewrites the working tree.

Two modes:
  rollback(n)     — go back n commits from HEAD on the current branch
  rollback(hash)  — jump directly to a specific commit hash

After a rollback the branch pointer is updated to the target commit,
so any subsequent 'nub commit' continues the chain from that point.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from .commit import read_commit, commit_history
from .refs import resolve_head, current_branch, write_ref, set_head_detached
from .tree import restore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wipe_working_tree(project_root: Path, objects_dir: Optional[Path] = None, current_tree_hash: Optional[str] = None) -> None:
    """
    Surgically remove only tracked files / directories from *project_root*.
    If current_tree_hash is provided, it only removes files that were in that tree.
    Otherwise, it falls back to a safer (but still broad) wipe of known tracked-like items.
    """
    vcs_path = project_root / ".vcs"
    
    if current_tree_hash and objects_dir:
        from .tree import list_tree
        try:
            entries = list_tree(current_tree_hash, objects_dir)
            # Remove files
            for mode, rel_path, blob_hash in entries:
                abs_path = project_root / rel_path
                if abs_path.exists() and abs_path.is_file():
                    abs_path.unlink()
            
            # Clean up empty directories
            for dirpath, dirnames, filenames in os.walk(project_root, topdown=False):
                dp = Path(dirpath)
                if dp.resolve() == vcs_path.resolve() or vcs_path in dp.parents:
                    continue
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
            return
        except Exception:
            pass 

    # Fallback/Safety: If no tree hash, we only remove things that aren't ignored by default
    from .tree import ALWAYS_IGNORE
    for item in project_root.iterdir():
        if item.resolve() == vcs_path.resolve():
            continue
        if item.name in ALWAYS_IGNORE:
            continue
        # We still want to be careful here. In NUB's simple model, 
        # let's only remove if it's likely part of the project.
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()


def _apply_commit(commit_hash: str, objects_dir: Path, project_root: Path, current_vcs_dir: Path) -> None:
    """Wipe the tracked working tree and restore the snapshot from *commit_hash*."""
    commit = read_commit(objects_dir, commit_hash)
    
    # Try to find current tree to wipe surgically
    current_head = resolve_head(current_vcs_dir)
    current_tree = None
    if current_head:
        try:
            current_tree = read_commit(objects_dir, current_head)["tree"]
        except:
            pass

    _wipe_working_tree(project_root, objects_dir, current_tree)
    restore(commit["tree"], objects_dir, project_root)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rollback_by_steps(
    project_root: Path,
    vcs_dir: Path,
    objects_dir: Path,
    steps: int,
) -> str:
    """
    Roll back *steps* commits on the current branch.
    Returns the commit hash that was restored.
    """
    if steps < 1:
        raise ValueError("Steps must be a positive integer.")

    head_hash = resolve_head(vcs_dir)
    if not head_hash:
        raise RuntimeError("Nothing to roll back — repository has no commits.")

    history = commit_history(objects_dir, head_hash)
    if steps >= len(history):
        raise ValueError(
            f"Cannot go back {steps} step(s): only {len(history)} commit(s) in history."
        )

    target = history[steps]
    target_hash = target["hash"]

    _apply_commit(target_hash, objects_dir, project_root, vcs_dir)

    # Move branch pointer (or stay detached if in detached-HEAD mode)
    branch = current_branch(vcs_dir)
    if branch:
        write_ref(vcs_dir, branch, target_hash)
    else:
        set_head_detached(vcs_dir, target_hash)

    return target_hash


def rollback_to_hash(
    project_root: Path,
    vcs_dir: Path,
    objects_dir: Path,
    commit_hash: str,
) -> str:
    """
    Roll back to a specific commit hash (full or unambiguous prefix).
    Returns the resolved full commit hash.
    """
    # Support short hashes by scanning objects
    full_hash = _resolve_partial_hash(objects_dir, commit_hash)

    _apply_commit(full_hash, objects_dir, project_root, vcs_dir)

    branch = current_branch(vcs_dir)
    if branch:
        write_ref(vcs_dir, branch, full_hash)
    else:
        set_head_detached(vcs_dir, full_hash)

    return full_hash


def _resolve_partial_hash(objects_dir: Path, prefix: str) -> str:
    """
    Given a full or partial hash, find the matching object.
    Raises ValueError on ambiguity or no match.
    """
    if len(prefix) == 40:
        # Assume it's already full; objects.load_blob will error if missing
        return prefix

    matches = []
    # Objects are stored as objects/<xx>/<rest>
    for bucket in objects_dir.iterdir():
        if not bucket.is_dir() or len(bucket.name) != 2:
            continue
        for obj_file in bucket.iterdir():
            full_hash = bucket.name + obj_file.name
            if full_hash.startswith(prefix):
                matches.append(full_hash)

    if not matches:
        raise ValueError(f"No commit found matching prefix '{prefix}'.")
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous prefix '{prefix}' matches {len(matches)} objects. "
            "Use a longer prefix."
        )
    return matches[0]


def list_rollback_targets(objects_dir: Path, vcs_dir: Path) -> list:
    """
    Return the commit history list for the current branch (for display).
    """
    head_hash = resolve_head(vcs_dir)
    if not head_hash:
        return []
    return commit_history(objects_dir, head_hash)
