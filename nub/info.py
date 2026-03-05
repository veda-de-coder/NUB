"""
info.py
Handles the NUB info command and branding.
"""
from pathlib import Path
from .init import find_vcs_root, vcs_dir
from .config import get_identity

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
