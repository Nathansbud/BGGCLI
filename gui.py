#!/Users/zackamiton/Code/BGGCLI/venv/bin/python

import urwid
import bggcli
import json
import os
from sys import argv

cache_path = os.path.join(os.path.dirname(__file__), "cache.json")
selected = None


CYAN = "\033[36;1m"
YELLOW = "\33[33;1m"
GREEN = "\033[32;1m"
RED = "\033[31;1m"

DEFAULT = "\033[0m"

def input_handler(key):
    global selected

    key = key.lower()
    if key in ('q', 'esc'):
        raise urwid.ExitMainLoop()
    elif key == 'up':
        active, idx = listbox.get_focus()
        listbox.set_focus(idx - 1 if idx > 0 else len(ui_items) - 1)
    elif key == 'down':
        active, idx = listbox.get_focus()
        listbox.set_focus(idx + 1 if idx < len(ui_items) - 1 else 0)
    elif key == 'enter':
        active, idx = listbox.get_focus()
        selected = idx
        raise urwid.ExitMainLoop()


if __name__ == '__main__':
    with open(cache_path) as cf: cache = json.load(cf)

    if len(argv) == 1 or argv[1] == '-help':
        print("Usage:\taddplay name [plays] [-nocache]")
        print("\tname: Name of board game")
        print("\t[plays]: Number of plays to log (1 by default)")
        print("\t[-nocache]: Ignore cache and force select menu to appear")
        exit(0)
    else:
        plays = 1
        use_cache = True
        title = argv[1].lower()
        if len(argv) > 2:
            if argv[-1] == "-nc": use_cache = False
            try:
                plays = int(argv[2])
                if plays < 1: raise ValueError
            except ValueError:
                print("Play count must be positive integer!")
                exit(-1)


        game_options = bggcli.get_games(title)
        if use_cache and title in cache and cache[title]['count'] >= 3:
            selected = cache[title]
        else:
            if not game_options:
                print("No items found!")
            else:
                game_items = [f'-> {game["name"]} ({game["year"]}) - ID: {game["idx"]}' for game in game_options]

                palette = [('reveal focus', 'black', 'dark cyan', 'standout')]
                ui_items = [urwid.Text(item) for item in game_items]
                content = urwid.SimpleListWalker([urwid.AttrMap(item, None, 'reveal focus') for item in ui_items])
                listbox = urwid.ListBox(content)
                header = urwid.AttrMap(urwid.Text("Select a BGG Game Item", wrap='clip'), 'header')
                top = urwid.Frame(listbox, header)
                loop = urwid.MainLoop(top, palette, unhandled_input=input_handler)
                loop.run()

                if isinstance(selected, int): selected = game_options[selected]

        if selected is not None:
            print(f"Adding {CYAN}{plays} {'plays' if plays > 1 else 'play'}{DEFAULT} to {YELLOW}{selected['name']} ({selected['year']}){DEFAULT}...")
            try:
                if bggcli.log_play(selected['idx'], plays=plays):
                    print(f"{GREEN}{'Plays added!' if plays > 1 else 'Play added!'}{DEFAULT}")
                else:
                    print(f"{RED}Play adding failed!{DEFAULT}")

                if not title in cache or cache[title]['idx'] != selected['idx']:
                    cache[title] = {'count': 1, 'idx': selected['idx'], 'name':selected['name'], 'year':selected['year']}
                else:
                    cache[title]['count'] += 1

                with open(cache_path, 'w+') as cf:
                    json.dump(cache, cf)
            except:
                print(f"{RED}Play adding failed!{DEFAULT}")

