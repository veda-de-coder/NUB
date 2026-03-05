"""
commit.py
Create and read snapshot objects with user identity and hash key.
"""
from datetime import datetime, timezone
from pathlib import Path
from .objects import save_blob, load_blob

def _format_commit(tree_hash, author_name, author_email, user_hash, message, branch, parent_hash=None) -> bytes:
    lines = [f"tree {tree_hash}"]
    if parent_hash:
        lines.append(f"parent {parent_hash}")
    lines += [
        f"author {author_name} <{author_email}>",
        f"key {user_hash}",
        f"date {datetime.now(timezone.utc).isoformat()}",
        f"flow {branch}",
        "",
        message.strip(),
    ]
    return "\n".join(lines).encode("utf-8")

def _parse_commit(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    header_block, _, message = text.partition("\n\n")
    commit = {"message": message.strip(), "parent": None}
    for line in header_block.splitlines():
        if line.startswith("tree "):    commit["tree"]   = line[5:].strip()
        elif line.startswith("parent "): commit["parent"] = line[7:].strip()
        elif line.startswith("author "): commit["author"] = line[7:].strip()
        elif line.startswith("key "):    commit["key"]    = line[4:].strip()
        elif line.startswith("date "):   commit["date"]   = line[5:].strip()
        elif line.startswith("flow "):   commit["flow"]   = line[5:].strip()
    return commit

def create_commit(objects_dir, tree_hash, author_name, author_email, user_hash, message, branch, parent_hash=None) -> str:
    raw = _format_commit(tree_hash, author_name, author_email, user_hash, message, branch, parent_hash)
    return save_blob(objects_dir, raw)

def read_commit(objects_dir: Path, commit_hash: str) -> dict:
    commit = _parse_commit(load_blob(objects_dir, commit_hash))
    commit["hash"] = commit_hash
    return commit

def commit_history(objects_dir: Path, start_hash: str) -> list:
    history, current, seen = [], start_hash, set()
    while current and current not in seen:
        seen.add(current)
        commit = read_commit(objects_dir, current)
        history.append(commit)
        current = commit.get("parent")
    return history
