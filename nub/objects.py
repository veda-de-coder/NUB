"""
objects.py — Hour 1
Save and load compressed blobs by SHA-1 hash.

Layout on disk (inside .vcs/objects/):
  ab/cdef1234...   ← first 2 chars = folder, rest = filename
                      (same strategy as Git, avoids huge flat directories)

Each file is zlib-compressed raw bytes.
"""

import zlib
from pathlib import Path

from .utils import sha1_hash


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _object_path(objects_dir: Path, digest: str) -> Path:
    """Convert a 40-char SHA-1 digest to its on-disk path."""
    return objects_dir / digest[:2] / digest[2:]


def _ensure_parents(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_blob(objects_dir: Path, data: bytes) -> str:
    """
    Compress *data* and write it to objects_dir under its SHA-1 hash.
    Returns the 40-char hex digest (the blob's permanent address).
    Idempotent: writing the same data twice is a no-op.
    """
    digest = sha1_hash(data)
    path = _object_path(objects_dir, digest)

    if not path.exists():
        _ensure_parents(path)
        path.write_bytes(zlib.compress(data, level=6))

    return digest


def load_blob(objects_dir: Path, digest: str) -> bytes:
    """
    Load and decompress the blob identified by *digest*.
    Raises FileNotFoundError if the hash is unknown.
    """
    path = _object_path(objects_dir, digest)
    if not path.exists():
        raise FileNotFoundError(f"Object not found: {digest}")
    return zlib.decompress(path.read_bytes())


def object_exists(objects_dir: Path, digest: str) -> bool:
    """Return True if the object is already stored."""
    return _object_path(objects_dir, digest).exists()
