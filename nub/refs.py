"""
refs.py — Hour 3
Manage branches — the sticky notes that point to commit hashes.

Layout inside .vcs/refs/:
    main          ← text file containing a 40-char commit hash
    experiment    ← another branch

HEAD (.vcs/HEAD) contains the *name* of the current branch, e.g.:
    ref: main
or a detached commit hash (rare, for direct-hash checkouts):
    <40-char-hash>
"""

from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# HEAD helpers
# ---------------------------------------------------------------------------

def read_head(vcs_dir: Path) -> str:
    """
    Return the content of HEAD as-is, e.g. 'ref: main' or a bare hash.
    """
    head_file = vcs_dir / "HEAD"
    if not head_file.exists():
        raise FileNotFoundError(".vcs/HEAD is missing — did you run 'nub init'?")
    return head_file.read_text().strip()


def current_branch(vcs_dir: Path) -> Optional[str]:
    """
    Return the branch name if HEAD points to a branch, else None
    (detached HEAD state).
    """
    head = read_head(vcs_dir)
    if head.startswith("ref: "):
        return head[5:].strip()
    return None


def resolve_head(vcs_dir: Path) -> Optional[str]:
    """
    Return the commit hash that HEAD currently points to, or None if the
    branch exists but has no commits yet.
    """
    head = read_head(vcs_dir)
    if head.startswith("ref: "):
        branch_name = head[5:].strip()
        return read_ref(vcs_dir, branch_name)
    # Detached HEAD — head IS the hash
    return head if head else None


def set_head_branch(vcs_dir: Path, branch_name: str) -> None:
    """Point HEAD at a branch (normal mode)."""
    (vcs_dir / "HEAD").write_text(f"ref: {branch_name}\n")


def set_head_detached(vcs_dir: Path, commit_hash: str) -> None:
    """Point HEAD directly at a commit hash (detached mode)."""
    (vcs_dir / "HEAD").write_text(commit_hash + "\n")


# ---------------------------------------------------------------------------
# Branch (ref) helpers
# ---------------------------------------------------------------------------

def _ref_path(vcs_dir: Path, branch_name: str) -> Path:
    return vcs_dir / "refs" / branch_name


def read_ref(vcs_dir: Path, branch_name: str) -> Optional[str]:
    """
    Return the commit hash stored in refs/<branch_name>, or None if the
    branch exists but is empty / doesn't exist yet.
    """
    path = _ref_path(vcs_dir, branch_name)
    if not path.exists():
        return None
    content = path.read_text().strip()
    return content if content else None


def write_ref(vcs_dir: Path, branch_name: str, commit_hash: str) -> None:
    """Advance a branch pointer to *commit_hash*."""
    path = _ref_path(vcs_dir, branch_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(commit_hash + "\n")


def list_branches(vcs_dir: Path) -> list:
    """Return sorted list of all branch names."""
    refs_dir = vcs_dir / "refs"
    if not refs_dir.exists():
        return []
    return sorted(p.name for p in refs_dir.iterdir() if p.is_file())


def branch_exists(vcs_dir: Path, branch_name: str) -> bool:
    return _ref_path(vcs_dir, branch_name).exists()


def create_branch(vcs_dir: Path, branch_name: str, from_hash: Optional[str] = None) -> None:
    """
    Create a new branch.  If *from_hash* is None the branch starts at the
    current HEAD commit (which may itself be None for an empty repo).
    Raises ValueError if branch already exists.
    """
    if branch_exists(vcs_dir, branch_name):
        raise ValueError(f"Branch '{branch_name}' already exists.")
    target = from_hash if from_hash is not None else resolve_head(vcs_dir)
    path = _ref_path(vcs_dir, branch_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((target + "\n") if target else "")


def delete_branch(vcs_dir: Path, branch_name: str) -> None:
    """Delete a branch ref.  Raises ValueError if it is the current branch."""
    if current_branch(vcs_dir) == branch_name:
        raise ValueError(f"Cannot delete the currently checked-out branch '{branch_name}'.")
    path = _ref_path(vcs_dir, branch_name)
    if not path.exists():
        raise FileNotFoundError(f"Branch '{branch_name}' does not exist.")
    path.unlink()
