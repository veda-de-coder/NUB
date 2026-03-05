"""
help.py — The NUB Help Guide and logic map.
"""
from pathlib import Path
from .ui import bold, magenta, cyan, yellow, dim
from .init import find_vcs_root, vcs_dir
from .config import get_identity

NUB_ASCII = r"""
...     ...                            ...     ..      
  .=*8888n.."%888:     x8h.     x8.      .=*8888x <"?88h.   
 X    ?8888f '8888   :88888> .x8888x.   X>  '8888H> '8888   
 88x. '8888X  8888>   `8888   `8888f   '88h. `8888   8888   
'8888k 8888X  '"*8h.   8888    8888'   '8888 '8888    "88>  
 "8888 X888X .xH8      8888    8888     `888 '8888.xH888x.  
   `8" X888!:888X      8888    8888       X" :88*~  `*8888> 
  =~`  X888 X888X      8888    8888     ~"   !"`      "888> 
   :h. X8*` !888X      8888    8888      .H8888h.      ?88  
  X888xX"   '8888..: -n88888x>"88888x-  :"^"88888h.    '!   
:~`888f     '*888*"    `%888"  4888!`   ^    "88888hx.+"    
    ""        `"`        `"      ""            ^"**""       
"""

HELP_TABLE = f"""
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

def print_help_guide():
    """Prints the comprehensive help guide with header and footer."""
    print(f"{NUB_ASCII}\n{bold(magenta('NUB — The Personal Version Vault'))}\n")
    print(HELP_TABLE)
    
    # Footer
    print(f"\n  {bold('NUB System Status & Support')}")
    print("  " + "=" * 45)
    
    try:
        root = find_vcs_root()
        vd = vcs_dir(root)
        print(f"  Project Root : {cyan(str(root))}")
        try:
            name, email, key = get_identity(vd)
            print(f"  Current User : {bold(name)} <{email}>")
            print(f"  User Hash Key: {magenta(key)}")
        except RuntimeError:
            print(f"  Current User : {yellow('(not authenticated)')}")
    except RuntimeError:
        print(f"  System Status: {yellow('Standing outside a repository')}")
    
    print(f"\n  {bold('Source & Support:')}")
    print(f"  NUB is open source. You can inspect the logic directly:")
    print(f"  - On GitHub: {cyan('https://github.com/veda-de-coder/NUB')}")
    print(f"  - Locally  : Use {bold('nub peek <file>')} (e.g., {dim('nub/cli.py')})")
    
    print(f"\n  {bold('Feedback & Issues:')}")
    print(f"  Reach out at: {bold(cyan('vedanarasimhan08@gmail.com'))}\n")
