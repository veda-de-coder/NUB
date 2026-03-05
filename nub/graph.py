"""
graph.py
A vertical ASCII and TUI commit graph generator.
"""
import curses
from pathlib import Path
from .commit import commit_history
from .refs import resolve_head
from .utils import short_hash

def get_graph_nodes(vd: Path, od: Path) -> list:
    """Returns a list of commit metadata for graphing."""
    head = resolve_head(vd)
    if not head:
        return []
    return commit_history(od, head)

def print_ascii_graph(vd: Path, od: Path):
    """Fallback ASCII graph."""
    history = get_graph_nodes(vd, od)
    if not history:
        print(" (No history yet) ")
        return
    for i, c in enumerate(history):
        char = "*" if i == 0 else "|"
        print(f" {char} [{short_hash(c['hash'])}] {c['message'][:40]}")

def draw_rounded_box(stdscr, y, x, h, w, color=0):
    """Draws a modern rounded box."""
    BOX_TL = "╭"
    BOX_TR = "╮"
    BOX_BL = "╰"
    BOX_BR = "╯"
    BOX_H  = "─"
    BOX_V  = "│"
    try:
        stdscr.addch(y, x, BOX_TL, color)
        stdscr.addch(y, x + w - 1, BOX_TR, color)
        stdscr.addch(y + h - 1, x, BOX_BL, color)
        stdscr.addch(y + h - 1, x + w - 1, BOX_BR, color)
        stdscr.addstr(y, x + 1, BOX_H * (w - 2), color)
        stdscr.addstr(y + h - 1, x + 1, BOX_H * (w - 2), color)
        for i in range(1, h - 1):
            stdscr.addch(y + i, x, BOX_V, color)
            stdscr.addch(y + i, x + w - 1, BOX_V, color)
    except curses.error:
        pass

def show_tui_graph(vd: Path, od: Path, root_name: str):
    """Launch the Gemini-style TUI graph."""
    history = get_graph_nodes(vd, od)
    total_snaps = len(history)

    def _tui(stdscr):
        curses.curs_set(0)
        curses.start_color()
        try: curses.use_default_colors()
        except: pass
        
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)

        selected_idx = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            h_max, w_max = stdscr.getmaxyx()
            list_h, list_w = h_max - 2, w_max - 4
            
            draw_rounded_box(stdscr, 0, 1, h_max, w_max - 2, curses.color_pair(4))
            title = f" NUB PROJECT: {root_name.upper()} "
            stdscr.addstr(0, 4, title, curses.color_pair(1) | curses.A_BOLD)
            footer = f" {total_snaps} Snaps | [Q] Quit "
            stdscr.addstr(h_max - 1, w_max - 4 - len(footer), footer, curses.color_pair(1))

            visible_rows = list_h - 2
            if selected_idx < scroll_offset: scroll_offset = selected_idx
            elif selected_idx >= scroll_offset + visible_rows: scroll_offset = selected_idx - visible_rows + 1

            for i in range(visible_rows):
                idx = scroll_offset + i
                if idx >= len(history): break
                c = history[idx]
                row_y = 1 + i + 1
                is_selected = (idx == selected_idx)
                
                if is_selected:
                    stdscr.addstr(row_y, 2, " " * (list_w - 2), curses.A_REVERSE | curses.color_pair(4))
                    style = curses.color_pair(1) | curses.A_BOLD
                    prefix = " │ "
                else:
                    style = curses.color_pair(3)
                    prefix = "   "

                line_content = f"{prefix}{short_hash(c['hash'])}  {c['message'][:list_w-35]:<{list_w-35}} {c.get('author','Unknown')[:15]}"
                try: stdscr.addstr(row_y, 2, line_content[:list_w-2], style)
                except curses.error: pass

            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')): break
            elif key == curses.KEY_UP and selected_idx > 0: selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < len(history) - 1: selected_idx += 1

    try: curses.wrapper(_tui)
    except: print_ascii_graph(vd, od)
