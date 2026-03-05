"""
commands.py — All NUB command logic.
"""
import os
import sys
import shutil
from pathlib import Path
from .init     import init_repo, find_vcs_root, vcs_dir, objects_dir
from .config   import get_identity, set_identity, clear_identity
from .tree     import snapshot, load_blob, restore as tree_restore, list_tree, get_blind_list
from .commit   import create_commit, read_commit, commit_history
from .refs     import (current_branch, resolve_head, write_ref,
                      list_branches, create_branch, delete_branch,
                      branch_exists, set_head_branch, read_ref)
from .rollback import (rollback_by_steps, rollback_to_hash,
                          _resolve_partial_hash)
from .utils    import short_hash, get_all_worlds, register_world, clean_universe
from .ui       import (SYM_OK, SYM_ERR, SYM_WARN, SYM_GO, 
                      green, yellow, red, cyan, magenta, bold, dim, draw_frame)
from .peek     import run_peek
from .graph    import show_tui_graph

def _require_root() -> Path:
    try:
        return find_vcs_root()
    except RuntimeError as exc:
        print(red(SYM_ERR), exc); sys.exit(1)

def cmd_start(args):
    target = Path(args.path).resolve() if args.path else Path.cwd()
    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            print(dim(f"  Created directory: {target}"))
        except Exception as e:
            print(red(SYM_ERR), f"Failed to create directory: {e}"); sys.exit(1)
    
    try:
        print(green(SYM_OK), init_repo(target))
    except FileExistsError as exc:
        print(yellow(SYM_WARN), exc); sys.exit(1)

def cmd_auth(args):
    root = _require_root()
    vd   = vcs_dir(root)
    if args.name or args.email:
        name, email = args.name, args.email
        if not name or not email:
            print(red(SYM_ERR), "Provide both --name and --email for authentication."); sys.exit(1)
        user_hash = set_identity(vd, name, email)
        print(green(SYM_OK), f"Identity Locked: {bold(name)} <{email}>")
        print(f"   Your Hash Key: {cyan(user_hash)}")
    else:
        print(bold("Current Identity:"))
        try:
            name, email, key = get_identity(vd)
            print(f"  Name : {cyan(name)}\n  Email: {cyan(email)}\n  Key  : [{magenta(key)}]")
        except RuntimeError as exc:
            print(dim(f"  (not set) — {exc}"))

def cmd_unauth(args):
    root = _require_root()
    vd   = vcs_dir(root)
    try:
        _, _, key = get_identity(vd)
        if not args.key:
            print(yellow(f"{SYM_WARN} To confirm logout, please provide your Hash Key: nub unauth --key {key}"))
            return
        if args.key.upper() != key.upper():
            print(red(f"{SYM_ERR} Key mismatch. Auth removal cancelled.")); sys.exit(1)
        clear_identity(vd)
        print(green(SYM_OK), "Identity cleared. You are now logged out.")
    except RuntimeError as exc:
        print(yellow(SYM_WARN), exc)

def cmd_snap(args):
    root   = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    try:
        name, email, user_hash = get_identity(vd)
    except RuntimeError as exc:
        print(red(SYM_ERR), exc); sys.exit(1)
    branch = current_branch(vd)
    if not branch:
        print(red(SYM_ERR), "HEAD is detached. Switch to a flow before snapping."); sys.exit(1)
    parent = resolve_head(vd)
    print(dim("  Taking snapshot..."))
    tree_hash = snapshot(root, od)
    if parent:
        last = read_commit(od, parent)
        if last["tree"] == tree_hash:
            print(yellow(SYM_WARN), "No changes detected since last snap."); return
    commit_hash = create_commit(od, tree_hash, name, email, user_hash, args.message, branch, parent)
    write_ref(vd, branch, commit_hash)
    print(green(SYM_OK), f"Snapped {bold(short_hash(commit_hash))} on flow {bold(magenta(branch))}")
    print(f"   Key: [{dim(user_hash)}] | {args.message}")

def cmd_past(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    head = resolve_head(vd)
    if not head:
        print(yellow("(no history yet)")); return
    history = commit_history(od, head)
    branch  = current_branch(vd)
    print(bold(f"\nProject Past — flow: {magenta(branch or '(detached)')}"))
    print(dim("=" * 60))
    for i, c in enumerate(history):
        marker = green(f"{SYM_GO} ") if i == 0 else "  "
        user_key = f"[{magenta(c.get('key','????'))}]"
        print(f"{marker}{bold(cyan(short_hash(c['hash'])))} {user_key}  "
              f"{dim(c.get('date','')[:19].replace('T',' '))}  "
              f"{bold(c.get('author','unknown'))}")
        print(f"       {c['message']}")
        if i < len(history) - 1:
            print(dim("       |"))
    print()

def cmd_flow(args):
    root = _require_root()
    vd   = vcs_dir(root)
    sub  = args.subcommand

    if sub in (None, "list"):
        branches = list_branches(vd)
        current  = current_branch(vd)
        if not branches:
            print(yellow("  (no flows)")); return
        print(bold("Flows:"))
        for b in branches:
            prefix = green("* ") if b == current else "  "
            tip    = read_ref(vd, b)
            tip_s  = f"  {dim(short_hash(tip))}" if tip else dim("  (no snaps)")
            print(f"  {prefix}{magenta(b)}{tip_s}")

    elif sub == "create":
        if not args.name:
            print(red(SYM_ERR), "Provide a flow name: nub flow create <name>"); sys.exit(1)
        try:
            create_branch(vd, args.name)
            print(green(SYM_OK), f"Flow '{bold(magenta(args.name))}' created.")
        except ValueError as exc:
            print(red(SYM_ERR), exc); sys.exit(1)

    elif sub == "switch":
        if not args.name:
            print(red(SYM_ERR), "Provide a flow name: nub flow switch <name>"); sys.exit(1)
        if not branch_exists(vd, args.name):
            print(red(SYM_ERR), f"Flow '{args.name}' does not exist."); sys.exit(1)
        set_head_branch(vd, args.name)
        tip = read_ref(vd, args.name)
        od  = objects_dir(root)
        if tip:
            vcs_path = root / ".vcs"
            for item in root.iterdir():
                if item.resolve() == vcs_path.resolve(): continue
                if (item.is_dir() and not item.is_symlink()):
                    shutil.rmtree(item)
                else:
                    item.unlink()
            commit = read_commit(od, tip)
            tree_restore(commit["tree"], od, root)
            print(green(SYM_OK), f"Switched to flow '{bold(magenta(args.name))}' @ {cyan(short_hash(tip))}")
            print(dim(f"  Working folder restored."))
        else:
            print(green(SYM_OK), f"Switched to flow '{bold(magenta(args.name))}' (empty).")

    elif sub == "delete":
        if not args.name:
            print(red(SYM_ERR), "Provide a flow name: nub flow delete <name>"); sys.exit(1)
        try:
            delete_branch(vd, args.name)
            print(green(SYM_OK), f"Flow '{bold(args.name)}' deleted.")
        except (ValueError, FileNotFoundError) as exc:
            print(red(SYM_ERR), exc); sys.exit(1)
    else:
        print(red(SYM_ERR), f"Unknown flow subcommand: '{sub}'"); sys.exit(1)

def cmd_back(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    if args.steps is not None and args.hash is not None:
        print(red(SYM_ERR), "Use either --steps or --hash, not both."); sys.exit(1)
    if args.steps is None and args.hash is None:
        print(red(SYM_ERR), "Provide --steps <n> or --hash <snap-hash>."); sys.exit(1)
    try:
        if args.steps is not None:
            target = rollback_by_steps(root, vd, od, args.steps)
            print(green(SYM_OK), f"Went back {args.steps} step(s) → {bold(cyan(short_hash(target)))}")
        else:
            target = rollback_to_hash(root, vd, od, args.hash)
            print(green(SYM_OK), f"Went back to snap {bold(cyan(short_hash(target)))}")
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(red(SYM_ERR), exc); sys.exit(1)

def cmd_now(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    branch = current_branch(vd)
    head   = resolve_head(vd)
    print(bold("\nNUB Status"))
    print(dim("=" * 40))
    print(f"  Flow   : {magenta(branch) if branch else yellow('(detached)')}")
    print(f"  Latest : {cyan(short_hash(head)) if head else yellow('(no snaps)')}")
    if head:
        c = read_commit(od, head)
        print(f"  Note   : {c['message'][:60]}")
        print(f"  Author : {bold(c.get('author',''))}")
        print(f"  Key    : {magenta(c.get('key',''))}")
    try:
        name, email, user_hash = get_identity(vd)
        print(f"  User   : {bold(name)} <{email}> [{magenta(user_hash)}]")
    except RuntimeError:
        print(f"  User   : {yellow('(not authenticated)')}")
    print()

def cmd_show(args):
    root = _require_root()
    od, vd = objects_dir(root), vcs_dir(root)
    commit_ref = args.snap_hash or resolve_head(vd)
    if not commit_ref:
        print(yellow("(no snaps)")); return
    try:
        full = _resolve_partial_hash(od, commit_ref)
    except ValueError as exc:
        print(red(SYM_ERR), exc); sys.exit(1)
    c = read_commit(od, full)
    print(bold(f"\nSnapshot  {cyan(full)}"))
    print(f"Author    {bold(c.get('author',''))}")
    print(f"Key       {magenta(c.get('key',''))}")
    print(f"Date      {dim(c.get('date',''))}")
    print(f"Flow      {magenta(c.get('flow',''))}")
    print(f"\n    {bold(c['message'])}\n")
    print(dim("Files in this snapshot:"))
    for mode, path, blob in list_tree(c["tree"], od):
        print(f"  {'x' if mode=='exec' else ' '} {path}  {dim(short_hash(blob))}")
    print()

def cmd_place(args):
    print(f"Standing in: {bold(os.getcwd())}")
    try:
        root = find_vcs_root()
        print(f"NUB root at: {cyan(str(root))}")
    except RuntimeError:
        print(dim("  (Not currently in a NUB repository)"))

def cmd_map(args):
    root = _require_root()
    print(f"\nNUB Map for: {bold(green(root.name))}")
    print(dim("=" * 40))
    
    blind_list = get_blind_list(root)
    vcs_dir_name = ".vcs"

    SYM_T = "|-- "
    SYM_L = "`-- "
    SYM_VV = "|   "

    def _walk(path, prefix=""):
        items = sorted([p for p in path.iterdir() if p.name not in (vcs_dir_name, ".nubblind")])
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            char = SYM_L if is_last else SYM_T
            
            is_blind = item.name in blind_list
            name_str = dim(f"{item.name} (blind)") if is_blind else (blue(item.name) if item.is_dir() else item.name)
            
            print(f"{dim(prefix)}{char}{name_str}")
            if item.is_dir() and not is_blind:
                next_prefix = prefix + (dim("    ") if is_last else dim(SYM_VV))
                _walk(item, next_prefix)

    _walk(root)
    print()

def cmd_blind(args):
    root = _require_root()
    blind_file = root / ".nubblind"
    
    if args.add:
        with open(blind_file, "a") as f:
            f.write(f"{args.add}\n")
        print(green(SYM_OK), f"NUB is now blind to: {bold(args.add)}")
    elif args.clear:
        if blind_file.exists():
            blind_file.unlink()
            print(green(SYM_OK), "Blind list cleared.")
    else:
        if not blind_file.exists():
            print(yellow("NUB is not currently blind to anything."))
        else:
            print(bold("Blind List (ignored files):"))
            print(dim(blind_file.read_text()))

def cmd_sight(args):
    root = _require_root()
    blind_file = root / ".nubblind"
    if not blind_file.exists():
        print(yellow(SYM_WARN), "NUB is already seeing everything clearly."); return
    
    lines = blind_file.read_text().splitlines()
    if args.target not in lines:
        print(yellow(f"{SYM_WARN} '{args.target}' is not in the blind list.")); return
    
    new_lines = [l for l in lines if l != args.target]
    if not new_lines:
        blind_file.unlink()
    else:
        blind_file.write_text("\n".join(new_lines) + "\n")
    print(green(SYM_OK), f"NUB has regained sight of: {bold(args.target)}")

def cmd_universe(args):
    if args.clean:
        removed = clean_universe()
        print(green(SYM_OK), f"Cleaned the universe. Removed {bold(str(removed))} dead path(s).")
        return

    worlds = get_all_worlds()
    if not worlds:
        print(yellow("  The NUB Universe is empty. Start your first project with 'nub start'!"))
        return
    
    print(bold(f"\nNUB Universe — {len(worlds)} Known World(s)"))
    print(dim("=" * 80))
    print(f"{bold('Path'):<45} | {bold('User'):<15} | {bold('Key')}")
    print(dim("-" * 80))
    
    for path_str in worlds:
        path = Path(path_str)
        vd = path / ".vcs"
        if not vd.exists():
            print(f"{dim(path_str):<45} | {red('(missing vcs)')}")
            continue
        
        try:
            name, _, user_hash = get_identity(vd)
            print(f"{cyan(path_str):<45} | {name:<15} | {magenta(user_hash)}")
        except:
            print(f"{path_str:<45} | {yellow('(no auth)')}")
    print()

def cmd_jump(args):
    worlds = get_all_worlds()
    matches = [w for w in worlds if args.query.lower() in w.lower()]
    
    if not matches:
        print(red(SYM_ERR), f"No vault found matching '{args.query}' in the universe."); sys.exit(1)
    
    print(bold(f"\nFound {len(matches)} matching vault(s):"))
    print(dim("=" * 60))
    for m in matches:
        print(f"{green(SYM_GO)} {cyan(m)}")
        cmd_text = f'cd "{m}"'
        print(f"   Command: {bold(cmd_text)}\n")

def cmd_peek(args):
    run_peek(args, SYM_ERR, SYM_WARN, red, yellow, blue, draw_frame)

def cmd_fork(args):
    root = _require_root()
    target_path = Path(args.target).resolve()
    
    if target_path.exists():
        print(red(SYM_ERR), f"Destination already exists: {target_path}"); sys.exit(1)
    
    print(dim(f"  Forking {root.name} to {target_path.name}..."))
    try:
        shutil.copytree(root, target_path)
        register_world(target_path)
        print(green(SYM_OK), f"Forked successfully to: {bold(target_path)}")
        print(dim("  The new directory is now a fully independent NUB repository."))
    except Exception as e:
        print(red(SYM_ERR), f"Fork failed: {e}"); sys.exit(1)

def cmd_graph(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    show_tui_graph(vd, od, root.name)

def cmd_shift(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    head = resolve_head(vd)
    if not head:
        print(yellow("! No previous snapshots to compare against.")); return
    
    target_rel = Path(args.file).as_posix()
    target_abs = root / args.file
    if not target_abs.exists():
        print(red(f"{SYM_ERR} File not found on disk: {args.file}")); sys.exit(1)
    
    commit = read_commit(od, head)
    tree_entries = list_tree(commit["tree"], od)
    
    old_content = []
    for mode, path, blob_hash in tree_entries:
        if path == target_rel:
            old_content = load_blob(od, blob_hash).decode("utf-8").splitlines()
            break
    
    new_content = target_abs.read_text().splitlines()
    
    print(bold(f"\nSHIFT: {args.file}"))
    draw_frame("PAST (Last Snap)", old_content, red)
    print(bold("        ▼ SHIFTING ▼"))
    draw_frame("NOW (On Disk)", new_content, green)
    print()
