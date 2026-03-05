#!/usr/bin/env python3
"""
cli.py — The entry-point. Lightweight delegation to modular logic.
"""
import argparse
import sys
from pathlib import Path

# Bootstrap: make sure 'nub' package is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from nub.ui       import red, SYM_ERR
from nub.help     import print_help_guide
from nub.commands import (
    cmd_start, cmd_auth, cmd_unauth, cmd_snap, cmd_past, 
    cmd_flow, cmd_back, cmd_now, cmd_show, cmd_place, 
    cmd_map, cmd_blind, cmd_sight, cmd_universe, 
    cmd_jump, cmd_peek, cmd_fork, cmd_graph, cmd_shift
)

class CustomParser(argparse.ArgumentParser):
    def error(self, message):
        if "invalid choice: 'help'" in message:
            print_help_guide()
            sys.exit(0)
        print(red(f"{SYM_ERR} Error: {message}\n"))
        self.print_help()
        sys.exit(2)

    def print_help(self, file=None):
        if self.prog == "nub":
            print_help_guide()
        else:
            super().print_help(file)

def build_parser():
    p = CustomParser(prog="nub", add_help=True)
    sub = p.add_subparsers(dest="command", metavar="<command>")

    sub.add_parser("help", help="Show the high-level guide.")

    # Define all subcommands with the descriptions and examples added previously
    p_start = sub.add_parser("start", help="Start a new repository",
        description="Initialize a new NUB repository. Creates a .vcs folder.",
        epilog="Example: nub start my_project")
    p_start.add_argument("path", nargs="?", help="Path to initialize")

    p_auth = sub.add_parser("auth", help="Authenticate user identity",
        description="Set name and email for signing snapshots.",
        epilog="Example: nub auth --name 'Veda' --email v@e.com")
    p_auth.add_argument("--name", help="Full name")
    p_auth.add_argument("--email", help="Email address")

    p_unauth = sub.add_parser("unauth", help="Clear identity",
        description="Remove identity from this vault. Requires Hash Key.",
        epilog="Example: nub unauth --key A1B2C3D4")
    p_unauth.add_argument("--key", help="Hash Key confirmation")

    p_snap = sub.add_parser("snap", help="Take a snapshot",
        description="Save tracked files to the current flow.",
        epilog="Example: nub snap -m 'Refactor'")
    p_snap.add_argument("-m", "--message", required=True, help="Snapshot message")

    sub.add_parser("past", help="Show history", description="View timeline of snaps.")
    sub.add_parser("now", help="Show status", description="Check flow and status.")
    sub.add_parser("place", help="Show directory", description="Display current path.")
    sub.add_parser("map", help="Show file layout", description="Render project tree.")
    
    p_uni = sub.add_parser("universe", help="Show all repositories",
        description="List known NUB projects. Use --clean to purge dead paths.")
    p_uni.add_argument("--clean", action="store_true", help="Purge registry")

    p_jmp = sub.add_parser("jump", help="Teleport to a repository",
        description="Quickly find and cd to a project.",
        epilog="Example: nub jump engine")
    p_jmp.add_argument("query", help="Search query")

    sub.add_parser("graph", help="Show commit graph", description="Open TUI node history.")

    p_fork = sub.add_parser("fork", help="Clone repository",
        description="Independent copy of the project.",
        epilog="Example: nub fork ../copy")
    p_fork.add_argument("target", help="Destination path")

    p_blind = sub.add_parser("blind", help="Ignore files")
    p_blind.add_argument("--add", help="Add to ignore list")
    p_blind.add_argument("--clear", action="store_true", help="Clear list")

    p_sight = sub.add_parser("sight", help="Unignore files")
    p_sight.add_argument("target", help="File to re-track")

    p_pk = sub.add_parser("peek", help="Read a file")
    p_pk.add_argument("file", help="File path")

    p_sh = sub.add_parser("shift", help="See changes")
    p_sh.add_argument("file", help="File to compare")

    p_show = sub.add_parser("show", help="Inspect snap")
    p_show.add_argument("snap_hash", nargs="?", help="Hash")

    p_flow = sub.add_parser("flow", help="Manage flows")
    p_flow.add_argument("subcommand", nargs="?", choices=["list","create","switch","delete"])
    p_flow.add_argument("name", nargs="?", help="Flow name")

    p_back = sub.add_parser("back", help="Revert snapshot")
    p_back.add_argument("--steps", type=int, help="Step count")
    p_back.add_argument("--hash", help="Target hash")

    return p

COMMANDS = {
    "start": cmd_start, "auth": cmd_auth, "unauth": cmd_unauth, "snap": cmd_snap,
    "past": cmd_past, "now": cmd_now, "place": cmd_place, "map": cmd_map,
    "universe": cmd_universe, "jump": cmd_jump, "peek": cmd_peek, "fork": cmd_fork,
    "graph": cmd_graph, "shift": cmd_shift, "show": cmd_show, "flow": cmd_flow,
    "back": cmd_back, "blind": cmd_blind, "sight": cmd_sight,
}

def main():
    parser = build_parser()
    args   = parser.parse_args()
    
    if args.command in (None, "help"):
        print_help_guide()
        sys.exit(0)
    
    handler = COMMANDS.get(args.command)
    if not handler:
        print(red(f"{SYM_ERR} Unknown command: '{args.command}'"))
        print_help_guide()
        sys.exit(1)
    
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted."); sys.exit(130)

if __name__ == "__main__":
    main()
