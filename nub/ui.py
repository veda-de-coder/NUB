"""
ui.py — Formatting, colours, and terminal symbols.
"""
import sys
from pathlib import Path

# Colour helpers
_USE_COLOR = sys.stdout.isatty()
def _c(code, text): return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text
def green(t):  return _c("32", t)
def yellow(t): return _c("33", t)
def cyan(t):   return _c("36", t)
def red(t):    return _c("31", t)
def blue(t):   return _c("34", t)
def magenta(t): return _c("35", t)
def white(t):   return _c("37", t)
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
SYM_V    = _get_symbol("│", "|")

def draw_frame(title, lines, color_func=dim):
    """Draws an ASCII box around a list of lines."""
    width = 60
    print(color_func("+--") + f" [ {bold(title)} ] " + color_func("-" * (width - len(title) - 8) + "+"))
    for line in lines:
        print(color_func("| ") + line.rstrip()[:width-4])
    print(color_func("+" + "-" * (width - 2) + "+"))
