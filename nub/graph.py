"""
graph.py
A sophisticated Gemini-style TUI for visualizing commit history.
"""
import curses
from pathlib import Path
from .commit import commit_history
from .refs import resolve_head
from .utils import short_hash
from .ui import bold, cyan, magenta, white, dim

def get_graph_nodes(vd: Path, od: Path) -> list:
    """Returns a list of commit metadata for graphing."""
    head = resolve_head(vd)
    if not head:
        return []
    return commit_history(od, head)

def draw_rounded_box(stdscr, y, x, h, w, color=0):
    """Draws a modern rounded box."""
    BOX_TL, BOX_TR = "╭", "╮"
    BOX_BL, BOX_BR = "╰", "╯"
    BOX_H, BOX_V   = "─", "│"
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
    except: pass

def show_tui_graph(vd: Path, od: Path, root_name: str):
    """Launch the enhanced Gemini-style TUI graph."""
    history = get_graph_nodes(vd, od)
    total_snaps = len(history)

    def _tui(stdscr):
        curses.curs_set(0)
        curses.start_color()
        try: curses.use_default_colors()
        except: pass
        
        # Pairs: 1=Cyan, 2=Magenta, 3=White, 4=Dim Blue, 5=Green
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_GREEN, -1)

        selected_idx = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            h_max, w_max = stdscr.getmaxyx()
            if h_max < 10 or w_max < 40:
                stdscr.addstr(0, 0, "Terminal too small!")
                stdscr.refresh()
                if stdscr.getch() in (ord('q'), ord('Q')): break
                continue

            # Layout: 
            # Header (2 rows)
            # Main Area (h_max - 6 rows) split into List (70%) and Graph (30%)
            # Detail Footer (4 rows)
            
            detail_h = 4
            list_h = h_max - detail_h - 2
            graph_w = 15
            list_w = w_max - graph_w - 4

            # 1. Main Border
            draw_rounded_box(stdscr, 0, 1, h_max, w_max - 2, curses.color_pair(4))
            stdscr.addstr(0, 4, f" NUB VAULT: {root_name.upper()} ", curses.color_pair(1) | curses.A_BOLD)
            
            # 2. List & Graph Separator
            for r in range(1, list_h + 1):
                try: stdscr.addch(r, w_max - graph_w - 2, "│", curses.color_pair(4))
                except: pass
            
            # 3. Footer Separator
            try: stdscr.addstr(h_max - detail_h - 1, 2, "─" * (w_max - 4), curses.color_pair(4))
            except: pass

            # 4. Render History List
            visible_rows = list_h - 1
            if selected_idx < scroll_offset: scroll_offset = selected_idx
            elif selected_idx >= scroll_offset + visible_rows: scroll_offset = selected_idx - visible_rows + 1

            for i in range(visible_rows):
                idx = scroll_offset + i
                if idx >= len(history): break
                c = history[idx]
                row_y = 1 + i + 1
                is_selected = (idx == selected_idx)
                
                style = curses.color_pair(1) | curses.A_BOLD if is_selected else curses.color_pair(3)
                if is_selected:
                    try: stdscr.addstr(row_y, 2, " " * (list_w + 1), curses.A_REVERSE | curses.color_pair(4))
                    except: pass

                h = short_hash(c['hash'], 6)
                msg = c['message'].split('\n')[0][:list_w - 15]
                date = c.get('date', '')[5:16].replace('T', ' ') # MM-DD HH:MM
                
                line = f" {h}  {date}  {msg}"
                try: stdscr.addstr(row_y, 2, line[:list_w], style)
                except: pass

            # 5. Render Visual Graph (Right Panel)
            for i in range(visible_rows):
                idx = scroll_offset + i
                if idx >= len(history): break
                row_y = 1 + i + 1
                node = "●" if idx == selected_idx else "○"
                color = curses.color_pair(5 if idx == 0 else 1)
                
                try:
                    stdscr.addstr(row_y, w_max - graph_w + 2, node, color)
                    if idx < len(history) - 1 and i < visible_rows - 1:
                        stdscr.addstr(row_y + 1, w_max - graph_w + 2, "│", curses.color_pair(4))
                except: pass

            # 6. Detail Footer
            if history and selected_idx < len(history):
                sel = history[selected_idx]
                stdscr.addstr(h_max - 4, 4, f"SNAP: {sel['hash']}", curses.color_pair(1))
                stdscr.addstr(h_max - 3, 4, f"AUTH: {sel.get('author','Unknown')}", curses.color_pair(2))
                full_msg = sel['message'].replace('\n', ' ')
                stdscr.addstr(h_max - 2, 4, f"NOTE: {full_msg[:w_max-12]}", curses.color_pair(3))

            stdscr.addstr(h_max - 1, w_max - 15, " [Q] EXIT ", curses.A_REVERSE)
            stdscr.refresh()
            
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')): break
            elif key == curses.KEY_UP and selected_idx > 0: selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < len(history) - 1: selected_idx += 1

    try: curses.wrapper(_tui)
    except:
        # Fallback to simple print
        print(f"\n{bold(cyan('NUB History Graph:'))}")
        for c in history:
            print(f" {magenta(short_hash(c['hash']))} | {c['message']}")
