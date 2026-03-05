#!/usr/bin/env python3
"""
cli.py — THE entry-point. All NUB commands go through here.
"""
import argparse
import os
import sys
from pathlib import Path

# Bootstrap: make sure 'nub' package is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from nub.init     import init_repo, find_vcs_root, vcs_dir, objects_dir
from nub.config   import get_identity, set_identity, clear_identity
from nub.tree     import snapshot, load_blob
from nub.commit   import create_commit, read_commit, commit_history
from nub.refs     import (current_branch, resolve_head, write_ref,
                          list_branches, create_branch, delete_branch,
                          branch_exists, set_head_branch, read_ref)
from nub.rollback import (rollback_by_steps, rollback_to_hash,
                          _resolve_partial_hash)
from nub.utils    import short_hash, get_all_worlds, register_world, clean_universe
from nub.info     import print_info
from nub.peek     import run_peek
from nub.graph    import show_tui_graph

# ── colour helpers ────────────────────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty()
def _c(code, text): return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text
def green(t):  return _c("32", t)
def yellow(t): return _c("33", t)
def cyan(t):   return _c("36", t)
def red(t):    return _c("31", t)
def blue(t):   return _c("34", t)
def magenta(t): return _c("35", t)
def bold(t):   return _c("1",  t)
def dim(t):    return _c("2",  t)

def _get_symbol(unicode_sym, ascii_fallback):
    try:
        unicode_sym.encode(sys.stdout.encoding or 'ascii')
        return unicode_sym
    except:
        return ascii_fallback

SYM_OK   = _get_symbol("✓", "[OK]")
SYM_ERR  = _get_symbol("✗", "[ERR]")
SYM_WARN = _get_symbol("!", "[!]")
SYM_GO   = _get_symbol("►", "->")

# ── helpers ───────────────────────────────────────────────────────────────────
def _require_root() -> Path:
    try:
        return find_vcs_root()
    except RuntimeError as exc:
        print(red(SYM_ERR), exc); sys.exit(1)

def _draw_frame(title, lines, color_func=dim):
    width = 60
    print(color_func("+--") + f" [ {bold(title)} ] " + color_func("-" * (width - len(title) - 8) + "+"))
    for line in lines:
        print(color_func("| ") + line.rstrip()[:width-4])
    print(color_func("+" + "-" * (width - 2) + "+"))

# ── command handlers ──────────────────────────────────────────────────────────
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
            import shutil
            from nub.tree import restore as tree_restore
            vcs_path = root / ".vcs"
            for item in root.iterdir():
                if item.resolve() == vcs_path.resolve(): continue
                shutil.rmtree(item) if (item.is_dir() and not item.is_symlink()) else item.unlink()
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
    from .tree import list_tree
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

    SYM_T = _get_symbol("├── ", "|-- ")
    SYM_L = _get_symbol("└── ", "`-- ")
    SYM_V = _get_symbol("│   ", "|   ")

    def _walk(path, prefix=""):
        items = sorted([p for p in path.iterdir() if p.name not in (vcs_dir_name, ".nubblind")])
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            char = SYM_L if is_last else SYM_T
            
            is_blind = item.name in blind_list
            name_str = dim(f"{item.name} (blind)") if is_blind else (blue(item.name) if item.is_dir() else item.name)
            
            print(f"{dim(prefix)}{char}{name_str}")
            if item.is_dir() and not is_blind:
                next_prefix = prefix + (dim("    ") if is_last else dim(SYM_V))
                _walk(item, next_prefix)

    from .tree import get_blind_list
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
    run_peek(args, SYM_ERR, SYM_WARN, red, yellow, blue, _draw_frame)

def cmd_info(args):
    print_info(bold, cyan, magenta, yellow)

def cmd_fork(args):
    import shutil
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
    from .tree import list_tree
    tree_entries = list_tree(commit["tree"], od)
    
    old_content = []
    for mode, path, blob_hash in tree_entries:
        if path == target_rel:
            old_content = load_blob(od, blob_hash).decode("utf-8").splitlines()
            break
    
    new_content = target_abs.read_text().splitlines()
    
    print(bold(f"\nSHIFT: {args.file}"))
    _draw_frame("PAST (Last Snap)", old_content, red)
    print(bold("        ▼ SHIFTING ▼"))
    _draw_frame("NOW (On Disk)", new_content, green)
    print()

# ── help table ────────────────────────────────────────────────────────────────
_HELP_TABLE = f"""
{bold(magenta("NUB — The Personal Version Vault"))}

{cyan("What is NUB?")}
  NUB is a lightweight, local-first version control system designed to keep 
  your project history safe without the complexity of traditional tools. 
  It takes "snaps" (snapshots) of your work, allowing you to travel back 
  in time or branch out into different "flows" of ideas.

{cyan("How to use NUB:")}
  1. {bold("nub start")}   - Initialize a new vault in your current folder.
  2. {bold("nub auth")}    - Set your identity so your snaps are signed.
  3. {bold("nub snap -m")} - Save your current progress forever.
  4. {bold("nub past")}    - Look at the timeline of your project.

{cyan("Command Reference & Git Translation:")}

  {bold("Setup & Identity")}
  NUB Command  | Git Equivalent      | Logic File   | Explanation
  -------------|---------------------|--------------|---------------------------
  start/init   | {yellow("git init")}            | {dim("init.py")}     | Begin project history.
  auth         | {yellow("git config")}          | {dim("config.py")}   | Set your name & email.
  unauth       | {yellow("(logout)")}            | {dim("config.py")}   | Clear local identity.
  universe     | {yellow("(registry)")}          | {dim("utils.py")}    | List all NUB projects.
  jump         | {yellow("(teleport)")}          | {dim("utils.py")}    | Find and go to a vault.

  {bold("Snapshots & History")}
  snap         | {yellow("git commit -am")}      | {dim("commit.py")}   | Save everything now.
  past         | {yellow("git log")}             | {dim("commit.py")}   | View timeline of snaps.
  show         | {yellow("git show")}            | {dim("commit.py")}   | Inspect a specific snap.
  now          | {yellow("git status")}          | {dim("refs.py")}     | Check flow and status.
  shift        | {yellow("git diff")}            | {dim("cli.py")}      | See changes since snap.
  info         | {yellow("(about)")}             | {dim("info.py")}     | Show branding & status.

  {bold("Time Travel & Flows")}
  flow         | {yellow("git branch/switch")}   | {dim("refs.py")}     | Manage work branches.
  back         | {yellow("git reset --hard")}    | {dim("rollback.py")} | Revert to a past state.
  graph        | {yellow("git log --graph")}     | {dim("graph.py")}    | Visual node history.
  fork         | {yellow("git clone (local)")}   | {dim("cli.py")}      | Clone project locally.

  {bold("Exploration & Visibility")}
  map          | {yellow("tree / ls -R")}        | {dim("tree.py")}     | See project structure.
  blind/sight  | {yellow(".gitignore")}          | {dim("tree.py")}     | Hide or reveal files.
  peek         | {yellow("cat / type")}          | {dim("peek.py")}     | Read a file's content.
  place        | {yellow("pwd")}                 | {dim("cli.py")}      | Show current location.

{dim("Use 'nub <command> -h' for more specific details on any command.")}
"""

class CustomParser(argparse.ArgumentParser):
    def error(self, message):
        # If they typed 'nub help', just show the help and exit cleanly
        if "invalid choice: 'help'" in message:
            self.print_help()
            sys.exit(0)
        
        print(red(f"Error: {message}\n"))
        self.print_help()
        sys.exit(2)

    def print_help(self, file=None):
        # If we are the top-level 'nub' parser, show the Vocabulary Guide.
        # Otherwise (subcommands), show the standard argparse help.
        if self.prog == "nub":
            print(_HELP_TABLE)
        else:
            super().print_help(file)

# ── parser ────────────────────────────────────────────────────────────────────
def build_parser():
    # Use 'add_help=True' for the main parser now, but we control display in print_help
    p = CustomParser(prog="nub", add_help=True)
    sub = p.add_subparsers(dest="command", metavar="<command>")

    # Add 'help' as an explicit command
    sub.add_parser("help", help="Show the high-level Vocabulary Guide and logic map.")

    p_start = sub.add_parser("start", 
        description="Initialize a new NUB repository in the specified directory. This creates a hidden .vcs folder to store your project history and configuration. If no path is provided, it will initialize in your current working directory.",
        epilog="Example: nub start my_project",
        help="Start a new repository")
    p_start.add_argument("path", nargs="?", help="Directory to start (default: cwd)")
    
    pi = sub.add_parser("init", help=argparse.SUPPRESS)
    pi.add_argument("path", nargs="?", help="Directory to start (default: cwd)")

    p_auth = sub.add_parser("auth", 
        description="Set or view your project identity. Providing both --name and --email will lock your identity and generate a unique Hash Key for signing snapshots. If run without arguments, it displays your current local identity.",
        epilog="Example: nub auth --name \"Alice\" --email alice@example.com",
        help="Authenticate user identity")
    p_auth.add_argument("--name",  help="Your full name")
    p_auth.add_argument("--email", help="Your email address")

    p_unauth = sub.add_parser("unauth", 
        description="Safely remove your identity from the current NUB repository. To prevent accidental logout, you must provide your unique Hash Key as confirmation. Once cleared, you will need to re-authenticate before taking new snapshots.",
        epilog="Example: nub unauth --key A1B2C3D4",
        help="Clear identity")
    p_unauth.add_argument("--key", help="Required: Your Hash Key to confirm")

    p_snap = sub.add_parser("snap", 
        description="Take a permanent snapshot of all tracked files in your project. This captures the exact state of your work and links it to the current flow. A mandatory message must be provided to describe the changes in this snap.",
        epilog="Example: nub snap -m \"Fix navigation bug\"",
        help="Take a snapshot of the project")
    p_snap.add_argument("-m", "--message", required=True, help="Snapshot message")

    sub.add_parser("past", 
        description="Display the chronological history of snapshots for the current flow. Each entry shows the snap hash, the author, the timestamp, and the commit message. It is the primary way to track the evolution of your project.",
        epilog="Example: nub past",
        help="Show project history")
    
    sub.add_parser("now", 
        description="Show your current position within the repository. This includes the name of the active flow, the hash of the latest snapshot, and your current authentication status. It provides a quick summary of 'where you are' right now.",
        epilog="Example: nub now",
        help="Show current status")
    
    sub.add_parser("place", 
        description="Display the absolute path of the directory you are currently standing in. It also identifies the root of the NUB repository if you are inside one. Useful for orienting yourself in deep directory structures.",
        epilog="Example: nub place",
        help="Show current directory")
    
    sub.add_parser("map", 
        description="Render a visual tree representation of all files and folders in the project. It respects the 'blind' list and skips the internal .vcs directory. This helps you understand the physical layout of your versioned files.",
        epilog="Example: nub map",
        help="Show project file layout")
    
    p_uni = sub.add_parser("universe", 
        description="List every NUB repository known to this machine. It scans the global registry to show the paths, active users, and hash keys of all your projects. Use --clean to remove entries that no longer exist on disk.",
        epilog="Example: nub universe --clean",
        help="Show all known repositories")
    p_uni.add_argument("--clean", action="store_true", help="Purge dead paths from the registry")

    p_jmp = sub.add_parser("jump", 
        description="Search for a known vault in your NUB Universe and provide the command to teleport (cd) there. This is the fastest way to move between different projects managed by NUB.",
        epilog="Example: nub jump my_web_app",
        help="Teleport to a known repository")
    p_jmp.add_argument("query", help="Project name or partial path to search for")

    sub.add_parser("info", 
        description="Display detailed information about the NUB system and the current repository. This includes the NUB ASCII logo, support contact info, and links to the source code for full transparency. It is the best place to start for new users.",
        epilog="Example: nub info",
        help="Display NUB info and system status")

    sub.add_parser("graph", 
        description="Open an interactive TUI to view the commit graph. It shows nodes and lines representing how snapshots are connected across flows. If the interactive mode is unavailable, it falls back to a clean ASCII representation.",
        epilog="Example: nub graph",
        help="Show visual commit graph")

    pf = sub.add_parser("fork", 
        description="Create a complete, independent copy of the current repository at a new location. This clones all files and the entire .vcs history into the destination path. The new directory is immediately registered as its own NUB world.",
        epilog="Example: nub fork ../my_project_v2",
        help="Fork this repository to a new path")
    pf.add_argument("target", help="Destination path for the fork")

    pb = sub.add_parser("blind", 
        description="Manage the 'blind' list to hide specific files or folders from NUB's sight. Adding a path here prevents it from being tracked in future snapshots. You can also clear the entire blind list to start fresh.",
        epilog="Example: nub blind --add logs/",
        help="Ignore files")
    pb.add_argument("--add",   help="Add a file/folder to the blind list")
    pb.add_argument("--clear", action="store_true", help="Clear the blind list")

    psgt = sub.add_parser("sight", 
        description="Restore visibility to a file or folder that was previously blinded. This removes the target from the .nubblind file, allowing NUB to track it in subsequent snapshots. It is the inverse of the 'blind' command.",
        epilog="Example: nub sight data.log",
        help="Unignore files")
    psgt.add_argument("target", help="The file or folder to re-track")

    p_pk = sub.add_parser("peek", 
        description="Quickly read and display the contents of a file directly in the terminal. It wraps the content in a clean frame for better readability. Unlike traditional tools, it can peek at NUB source files even if you aren't in a repo.",
        epilog="Example: nub peek nub/cli.py",
        help="Read a file")
    p_pk.add_argument("file",  help="The file to read")

    p_sh = sub.add_parser("shift", 
        description="Compare the current state of a file on disk against its version in the latest snapshot. It displays a 'Past' vs 'Now' view to show exactly what has shifted. Useful for reviewing changes before taking a new snap.",
        epilog="Example: nub shift main.py",
        help="See changes")
    p_sh.add_argument("file",  help="The file to compare")

    ps = sub.add_parser("show", 
        description="Inspect the full details of a specific snapshot. If no hash is provided, it defaults to the latest snap in the current flow. It lists the author, date, message, and every file captured in that snapshot.",
        epilog="Example: nub show a1b2c3d",
        help="Inspect a specific snapshot")
    ps.add_argument("snap_hash", nargs="?", help="Snapshot hash (default: latest)")

    p_flow = sub.add_parser("flow", 
        description="Manage your project's work flows (branches). You can list all flows, create new ones, switch between them, or delete old ones. Switching flows will update your working directory to match that flow's latest snap.",
        epilog="Example: nub flow switch experimental",
        help="Manage work flows")
    p_flow.add_argument("subcommand", nargs="?",
                    choices=["list","create","switch","delete"],
                    help="list | create | switch | delete")
    p_flow.add_argument("name", nargs="?", help="Flow name")

    pr = sub.add_parser("back", 
        description="Travel back in time to a previous snapshot state. You can specify a number of steps to jump back or provide a specific snap hash. This updates both the branch pointer and your physical files on disk.",
        epilog="Example: nub back --steps 2",
        help="Go back to a previous snapshot")
    pr.add_argument("--steps", type=int, metavar="N", help="Go back N snaps")
    pr.add_argument("--hash",  metavar="HASH",        help="Go back to a specific snap hash")

    return p

COMMANDS = {
    "start": cmd_start, "init": cmd_start, "auth": cmd_auth, "unauth": cmd_unauth,
    "snap": cmd_snap, "past": cmd_past, "now": cmd_now, 
    "show": cmd_show, "flow": cmd_flow, "back": cmd_back,
    "place": cmd_place, "map": cmd_map, "blind": cmd_blind, "sight": cmd_sight,
    "universe": cmd_universe, "peek": cmd_peek, "shift": cmd_shift,
    "info": cmd_info, "fork": cmd_fork, "graph": cmd_graph,
    "jump": cmd_jump,
}

def main():
    parser = build_parser()
    args   = parser.parse_args()
    
    # Check for 'help' command
    if args.command == "help":
        parser.print_help()
        sys.exit(0)
        
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    handler = COMMANDS.get(args.command)
    if not handler:
        print(red(SYM_ERR), f"Unknown command: '{args.command}'")
        parser.print_help(); sys.exit(1)
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted."); sys.exit(130)

if __name__ == "__main__":
    main()
