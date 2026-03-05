"""
info.py
Handles the NUB info command and branding.
"""
from pathlib import Path
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

def print_info(bold, cyan, magenta, yellow):
    """Print system status and branding."""
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
