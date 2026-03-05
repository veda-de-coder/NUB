#!/usr/bin/env bash
# install.sh — Hour 6
# Run this once per machine to make the `nub` command available globally.
# Usage:  bash install.sh
#
# What it does:
#   1. Finds this script's directory (where cli.py lives inside nub/)
#   2. Writes a tiny `nub` wrapper into /usr/local/bin (or ~/bin on macOS)
#   3. Makes the wrapper executable
#
# After installation, any user with access to this machine can type:
#   nub init / nub commit / nub log / etc.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_PATH="$SCRIPT_DIR/nub/cli.py"

if [[ ! -f "$CLI_PATH" ]]; then
    echo "✗  Cannot find nub/cli.py in $SCRIPT_DIR"
    exit 1
fi

# Resolve Python 3 interpreter
PYTHON=$(command -v python3 || command -v python || true)
if [[ -z "$PYTHON" ]]; then
    echo "✗  Python 3 is required but not found.  Install Python 3 first."
    exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
if [[ "$PY_VERSION" != "3" ]]; then
    echo "✗  Python 3 is required (found Python $PY_VERSION)."
    exit 1
fi

# Pick install directory
if [[ -w /usr/local/bin ]]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

WRAPPER="$INSTALL_DIR/nub"

cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# Auto-generated wrapper — do not edit.
exec "$PYTHON" "$CLI_PATH" "\$@"
EOF

chmod +x "$WRAPPER"

echo "✓  Installed nub → $WRAPPER"
echo "   Python: $PYTHON"
echo ""
echo "   If $INSTALL_DIR is not in your PATH, add this to ~/.bashrc or ~/.zshrc:"
echo "   export PATH=\"$INSTALL_DIR:\$PATH\""
echo ""
echo "   Quick-start:"
echo "     cd /path/to/your/project"
echo "     nub init"
echo "     nub config --name \"Your Name\" --email you@example.com"
echo "     nub commit -m \"Initial commit\""
