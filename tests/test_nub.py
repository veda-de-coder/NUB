import os
import shutil
import pytest
from pathlib import Path
from nub.init import init_repo, vcs_dir, objects_dir
from nub.config import set_identity
from nub.tree import snapshot
from nub.commit import create_commit, read_commit
from nub.refs import write_ref, current_branch, resolve_head, set_head_branch
from nub.rollback import rollback_by_steps, rollback_to_hash

@pytest.fixture
def temp_repo(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    init_repo(repo_dir)
    set_identity(vcs_dir(repo_dir), "Tester", "tester@example.com")
    return repo_dir

def test_init_repo(tmp_path):
    repo_dir = tmp_path / "new_repo"
    repo_dir.mkdir()
    msg = init_repo(repo_dir)
    assert (repo_dir / ".vcs").is_dir()
    assert "Initialised empty NUB repository" in msg

def test_snap_and_rollback(temp_repo):
    vd, od = vcs_dir(temp_repo), objects_dir(temp_repo)
    
    # Create a file and snap it
    file1 = temp_repo / "hello.txt"
    file1.write_text("Hello World")
    
    tree_hash = snapshot(temp_repo, od)
    commit_hash = create_commit(od, tree_hash, "Tester", "tester@example.com", "HASH123", "First Snap", "main")
    write_ref(vd, "main", commit_hash)
    
    # Create another file and snap it
    file2 = temp_repo / "world.txt"
    file2.write_text("Goodbye World")
    
    tree_hash2 = snapshot(temp_repo, od)
    commit_hash2 = create_commit(od, tree_hash2, "Tester", "tester@example.com", "HASH123", "Second Snap", "main", commit_hash)
    write_ref(vd, "main", commit_hash2)
    
    assert file2.exists()
    
    # Rollback 1 step
    rollback_by_steps(temp_repo, vd, od, 1)
    
    assert file1.exists()
    assert not file2.exists()

def test_untracked_files_preserved_during_rollback(temp_repo):
    vd, od = vcs_dir(temp_repo), objects_dir(temp_repo)
    
    # Snap 1
    (temp_repo / "tracked.txt").write_text("tracked")
    th1 = snapshot(temp_repo, od)
    ch1 = create_commit(od, th1, "T", "t@e.com", "K", "m1", "main")
    write_ref(vd, "main", ch1)
    
    # Snap 2
    (temp_repo / "tracked2.txt").write_text("tracked2")
    th2 = snapshot(temp_repo, od)
    ch2 = create_commit(od, th2, "T", "t@e.com", "K", "m2", "main", ch1)
    write_ref(vd, "main", ch2)
    
    # Create untracked file
    untracked = temp_repo / "untracked.txt"
    untracked.write_text("I should survive")
    
    # Rollback
    rollback_by_steps(temp_repo, vd, od, 1)
    
    assert (temp_repo / "tracked.txt").exists()
    assert not (temp_repo / "tracked2.txt").exists()
    assert untracked.exists(), "Untracked file was deleted during rollback!"
    assert untracked.read_text() == "I should survive"

def test_flow_management(temp_repo):
    vd = vcs_dir(temp_repo)
    from nub.refs import create_branch, branch_exists, list_branches
    
    create_branch(vd, "feature")
    assert branch_exists(vd, "feature")
    assert "feature" in list_branches(vd)
    assert "main" in list_branches(vd)

def test_partial_hash_resolution(temp_repo):
    vd, od = vcs_dir(temp_repo), objects_dir(temp_repo)
    (temp_repo / "f.txt").write_text("content")
    th = snapshot(temp_repo, od)
    ch = create_commit(od, th, "T", "t@e.com", "K", "msg", "main")
    
    from nub.rollback import _resolve_partial_hash
    resolved = _resolve_partial_hash(od, ch[:8])
    assert resolved == ch
