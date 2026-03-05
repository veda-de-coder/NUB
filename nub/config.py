"""
config.py
Enhanced identity management with persistent Hash Keys.
"""
import json
import hashlib
from pathlib import Path
from typing import Tuple

def _config_path(vcs_dir: Path) -> Path:
    return vcs_dir / "config.json"

def _generate_user_hash(email: str) -> str:
    """Generate a stable 8-char hash key based ONLY on email."""
    seed = email.strip().lower().encode("utf-8")
    return hashlib.sha1(seed).hexdigest()[:8].upper()

def get_identity(vcs_dir: Path) -> Tuple[str, str, str]:
    path = _config_path(vcs_dir)
    if not path.exists():
        raise RuntimeError("No identity found. Run: nub auth --name \"Name\" --email \"email\"")
    data = json.loads(path.read_text())
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    user_hash = data.get("user_hash", "").strip()
    if not name or not email:
        raise RuntimeError("Identity incomplete. Run: nub auth")
    return name, email, user_hash

def set_identity(vcs_dir: Path, name: str, email: str) -> str:
    path = _config_path(vcs_dir)
    user_hash = _generate_user_hash(email)
    data = {"name": name.strip(), "email": email.strip().lower(), "user_hash": user_hash}
    path.write_text(json.dumps(data, indent=2) + "\n")
    return user_hash

def clear_identity(vcs_dir: Path):
    path = _config_path(vcs_dir)
    if path.exists():
        path.unlink()

def show_identity(vcs_dir: Path) -> str:
    try:
        name, email, user_hash = get_identity(vcs_dir)
        return f"  Name : {name}\n  Email: {email}\n  Key  : [{user_hash}]"
    except RuntimeError as exc:
        return f"  (not set) — {exc}"
