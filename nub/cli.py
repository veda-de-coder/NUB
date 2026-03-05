#!/usr/bin/env python3
"""
cli.py — THE entry-point. All NUB commands go through here.
"""
import argparse
import os
import sys
import difflib
from pathlib import Path

# Bootstrap: make sure 'nub' package is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from nub.init     import init_repo, find_vcs_root, vcs_dir, objects_dir
from nub.config   import get_identity, set_identity, show_identity, clear_identity
from nub.tree     import snapshot, list_tree, get_blind_list, load_blob
from nub.commit   import create_commit, read_commit, commit_history
from nub.refs     import (current_branch, resolve_head, write_ref,
                          list_branches, create_branch, delete_branch,
                          branch_exists, set_head_branch, read_ref)
from nub.rollback import (rollback_by_steps, rollback_to_hash,
                          _resolve_partial_hash)
from nub.utils    import short_hash, get_all_worlds, register_world
from nub.graph    import generate_graph

# ── NUB ASCII ART ─────────────────────────────────────────────────────────────
NUB_ASCII = r"""
 ██████   █████ █████  █████ ███████████ 
▒▒██████ ▒▒███ ▒▒███  ▒▒███ ▒▒███▒▒▒▒▒███
 ▒███▒███ ▒███  ▒███   ▒███  ▒███    ▒███
 ▒███▒▒███▒███  ▒███   ▒███  ▒██████████ 
 ▒███ ▒▒██████  ▒███   ▒███  ▒███▒▒▒▒▒███
 ▒███  ▒▒█████  ▒███   ▒███  ▒███    ▒███
 █████  ▒▒█████ ▒▒████████   ███████████ 
▒▒▒▒▒    ▒▒▒▒▒   ▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒▒
"""

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
    except UnicodeEncodeError:
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

# ── commands ──────────────────────────────────────────────────────────────────
def cmd_start(args):
    target = Path(args.path).resolve() if args.path else Path.cwd()
    try:
        print(green(SYM_OK), init_repo(target))
    except FileExistsError as exc:
        print(yellow(SYM_WARN), exc); sys.exit(1)

def cmd_auth(args):
    root = _require_root()
    vd   = vcs_dir(root)
    if args.name or args.email:
        name  = args.name
        email = args.email
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
        print(yellow("NUB is already seeing everything clearly.")); return
    
    lines = blind_file.read_text().splitlines()
    if args.target not in lines:
        print(yellow(f"! '{args.target}' is not in the blind list.")); return
    
    new_lines = [l for l in lines if l != args.target]
    if not new_lines:
        blind_file.unlink()
    else:
        blind_file.write_text("\n".join(new_lines) + "\n")
    print(green(SYM_OK), f"NUB has regained sight of: {bold(args.target)}")

def cmd_universe(args):
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

def cmd_peek(args):
    # Don't strictly require a root to peek at files (for transparency)
    try:
        root = find_vcs_root()
        target = root / args.file
    except RuntimeError:
        target = Path(args.file)
        
    if not target.exists():
        print(red(f"{SYM_ERR} File not found: {args.file}")); sys.exit(1)
    
    if target.is_dir():
        print(yellow(f"{SYM_WARN} '{args.file}' is a directory. Listing contents:"))
        for item in sorted(target.iterdir()):
            print(f"  {'/' if item.is_dir() else ' '} {item.name}")
        return

    try:
        content = target.read_text().splitlines()
        _draw_frame(f"PEEK: {args.file}", content, blue)
    except Exception as e:
        print(red(f"{SYM_ERR} Could not read file: {e}")); sys.exit(1)

def cmd_info(args):
    # Plain, no-color output as requested
    print(NUB_ASCII)

    print(f"  {bold('NUB Version Vault')} — Beta Prototype")
    print("  " + "=" * 45)
    
    try:
        root = find_vcs_root()
        vd = vcs_dir(root)
        print(f"  Project Root : {root}")
        try:
            name, email, key = get_identity(vd)
            print(f"  Current User : {name} <{email}>")
            print(f"  User Hash Key: {key}")
        except RuntimeError:
            print(f"  Current User : (not authenticated)")
    except RuntimeError:
        print(f"  System Status: Standing outside a repository")
    
    print(f"\n  {bold('Source & Support:')}")
    print(f"  NUB is open source. You can inspect the logic directly:")
    print(f"  - On GitHub: https://github.com/veda-de-coder/NUB")
    print(f"  - Locally  : Use nub peek <file> (e.g., nub/cli.py)")
    
    print(f"\n  {bold('Feedback & Issues:')}")
    print(f"  Have suggestions or found a bug? Reach out at:")
    print(f"  vedanarasimhan08@gmail.com")
    print()

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
    import curses
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    
    graph_data = generate_graph(vd, od)
    
    def _tui(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.clear()
        
        max_y, max_x = stdscr.getmaxyx()
        
        for i, line in enumerate(graph_data[:max_y-2]):
            stdscr.addstr(i, 2, line[:max_x-4])
        
        stdscr.addstr(max_y-1, 0, " [ Press any key to exit graph ] ", curses.A_REVERSE)
        stdscr.refresh()
        stdscr.getch()

    try:
        curses.wrapper(_tui)
    except Exception as e:
        # Fallback if curses fails
        from nub.graph import print_ascii_graph
        print_ascii_graph(vd, od)

def cmd_shift(args):
    root = _require_root()
    vd, od = vcs_dir(root), objects_dir(root)
    head = resolve_head(vd)
    if not head:
        print(yellow("! No previous snapshots to compare against.")); return
    
    target_rel = Path(args.file).as_posix()
    target_abs = root / args.file
    if not target_abs.exists():
        print(red(f"✗ File not found on disk: {args.file}")); sys.exit(1)
    
    commit = read_commit(od, head)
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

{cyan("Command Reference & Logic Map:")}

  {bold("Setup & Identity")}
  start/init   | {dim("init.py")}     | Begin a new project history.
  auth         | {dim("config.py")}   | Sign in with your name and email.
  unauth       | {dim("config.py")}   | Sign out and clear local identity.
  universe     | {dim("utils.py")}    | List all NUB projects on this machine.

  {bold("Snapshots & History")}
  snap         | {dim("commit.py")}   | Save everything exactly as it is now.
  past         | {dim("commit.py")}   | View the chronological list of snaps.
  show         | {dim("commit.py")}   | Inspect the contents of a specific snap.
  now          | {dim("refs.py")}     | Check your current flow and latest snap.
  shift        | {dim("cli.py")}      | See what changed since the last snap.
  info         | {dim("cli.py")}      | Show NUB identity, status, and ASCII art.

  {bold("Time Travel & Flows")}
  flow         | {dim("refs.py")}     | Create, switch, or delete work branches.
  back         | {dim("rollback.py")} | Revert your project to a previous state.
  graph        | {dim("graph.py")}    | View visual node-based history.
  fork         | {dim("cli.py")}      | Clone this project to a new location.

  {bold("Exploration & Visibility")}
  map          | {dim("tree.py")}     | See the structure of your project.
  blind/sight  | {dim("tree.py")}     | Hide or reveal files from NUB's sight.
  peek         | {dim("cli.py")}      | Quickly read a file's content.
  place        | {dim("cli.py")}      | Show where you are in the universe.

{dim("Use 'nub <command> -h' for more specific details on any command.")}
"""

class CustomParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Error: {message}\n")
        self.print_help()
        sys.exit(2)

    def print_help(self, file=None):
        print(_HELP_TABLE)

# ── parser ────────────────────────────────────────────────────────────────────
def build_parser():
    p = CustomParser(prog="nub", add_help=False)
    p.add_argument("-h", "--help", action="store_true")
    sub = p.add_subparsers(dest="command", metavar="<command>")

    p_start = sub.add_parser("start",     help="Start a new repository")
    p_start.add_argument("path", nargs="?", help="Directory to start (default: cwd)")
    pi = sub.add_parser("init", help=argparse.SUPPRESS)
    pi.add_argument("path", nargs="?", help="Directory to start (default: cwd)")

    p_auth = sub.add_parser("auth", help="Authenticate user identity")
    p_auth.add_argument("--name",  help="Your full name")
    p_auth.add_argument("--email", help="Your email address")

    p_unauth = sub.add_parser("unauth", help="Clear identity")
    p_unauth.add_argument("--key", help="Required: Your Hash Key to confirm")

    p_snap = sub.add_parser("snap",  help="Take a snapshot of the project")
    p_snap.add_argument("-m", "--message", required=True, help="Snapshot message")

    sub.add_parser("past",           help="Show project history")
    sub.add_parser("now",            help="Show current status")
    sub.add_parser("place",          help="Show current directory")
    sub.add_parser("map",            help="Show project file layout")
    sub.add_parser("universe",       help="Show all known repositories")
    sub.add_parser("info",           help="Display NUB info and system status")
    sub.add_parser("graph",          help="Show visual commit graph")

    pf = sub.add_parser("fork",      help="Fork this repository to a new path")
    pf.add_argument("target", help="Destination path for the fork")

    pb = sub.add_parser("blind",      help="Ignore files")
    pb.add_argument("--add",   help="Add a file/folder to the blind list")
    pb.add_argument("--clear", action="store_true", help="Clear the blind list")

    psgt = sub.add_parser("sight",     help="Unignore files")
    psgt.add_argument("target", help="The file or folder to re-track")

    p_pk = sub.add_parser("peek",      help="Read a file")
    p_pk.add_argument("file",  help="The file to read")

    p_sh = sub.add_parser("shift",     help="See changes")
    p_sh.add_argument("file",  help="The file to compare")

    ps = sub.add_parser("show",      help="Inspect a specific snapshot")
    ps.add_argument("snap_hash", nargs="?", help="Snapshot hash (default: latest)")

    p_flow = sub.add_parser("flow",      help="Manage work flows")
    p_flow.add_argument("subcommand", nargs="?",
                    choices=["list","create","switch","delete"],
                    help="list | create | switch | delete")
    p_flow.add_argument("name", nargs="?", help="Flow name")

    pr = sub.add_parser("back",      help="Go back to a previous snapshot")
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
}

def main():
    parser = build_parser()
    args   = parser.parse_args()
    if args.help:
        parser.print_help(); sys.exit(0)
    if not args.command:
        parser.print_help(); sys.exit(0)
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
