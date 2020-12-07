#!/Users/zackamiton/Code/BGGCLI/venv/bin/python
import urwid
import link
import json
import os
from sys import argv, platform
import argparse
import webbrowser

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

def choose_title():
    if platform == 'ios':
        import dialogs 
        
        sections = [
            {"title":"Game: ", "type": "text", "key":"game"},
            {"title":"Plays: ", "type":"number", "key":"plays", "value": "1"}
        ]
        choices = dialogs.form_dialog("Game Played", fields=sections) or {}
        
        try:
            plays = int(choices.get('plays', 0))
            game = choices.get('game')
            if game and plays > 0:
                game_options = link.get_games(game)
                if game_options:
                    selected = dialogs.list_dialog("Choose Title", [f'{g["name"]} ({g["year"]}) - {g["idx"]}' for g in game_options])		
                    if selected: 
                        idx = selected.split('-')[-1]
                        link.log_play(idx, plays)			
                        dialogs.alert("Add Success", f"Added {str(plays) + ' plays' if plays != 1 else str(plays) + ' play'} to {game}", "Close", hide_cancel_button=True)
                else:
                    dialogs.alert(f"No entries found for {game} on BoardGameGeek!")
        except ValueError:
            dialogs.alert("Play count must be a number!")
    else:
        raise ImportError("Cannot run choose_title on a non-iOS device!")
                
if __name__ == '__main__':
    if platform != 'ios':
        with open(cache_path) as cf: cache = json.load(cf)
        parser = argparse.ArgumentParser(prog='bgg', allow_abbrev=True)

        mutex = parser.add_mutually_exclusive_group()
        mutex.add_argument('-a', '--add', nargs='+', metavar=('title', '?plays'), help="add plays by title")
        mutex.add_argument('-s', '--summary', nargs='?', metavar='?days', type=int, const=0, default=-1, help='get game summary for last # of days (or full history if omitted)')
        mutex.add_argument('-o', '--open', action='store_true', help='open boardgamegeek')

        parser.add_argument('-n', '--nocache', action='store_true', help='ignore cache')
        parser.add_argument('-m', '--sortmode', default='title', const='title', nargs='?', choices=['title', 'plays'], help='mode to sort summary by')

        args = vars(parser.parse_args())
        add, summary = args.get('add'), args.get('summary')
        
        if add is not None:
            plays = 1
            if len(add) == 2:
                try:
                    plays = int(add[1])
                    if plays < 1: raise ValueError
                except ValueError:
                    parser.error("Play argument must be a positive number (preferably an integer)!")

            use_cache = not args.get('nocache')
            title = add[0].lower()
            game_options = link.get_games(title)
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
                    if link.log_play(selected['idx'], plays=plays):
                        print(f"{GREEN}{'Plays added!' if plays > 1 else 'Play added!'}{DEFAULT}")
                    else:
                        print(f"{RED}Play adding failed!{DEFAULT}")

                    if not title in cache or cache[title]['idx'] != selected['idx']:
                        cache[title] = {'count': 1, 'idx': selected['idx'], 'name': selected['name'],
                                        'year': selected['year']}
                    else:
                        cache[title]['count'] += 1

                    with open(cache_path, 'w+') as cf:
                        json.dump(cache, cf)
                except:
                    print(f"{RED}Play adding failed!{DEFAULT}")
        elif summary >= 0:
            play_data = link.get_plays(None if summary < 1 else summary)
            game_data = {}
            for play in play_data:
                if play['name'] in game_data: game_data[play['name']] += play['plays']
                else: game_data[play['name']] = play['plays']


            if args.get('sortmode') == 'title': summary_set = sorted(game_data.items(), key=lambda gd: gd[0] if not gd[0].lower().startswith("the ") else gd[0][4:])
            elif args.get('sortmode') == 'plays': summary_set = reversed(sorted(game_data.items(), key=lambda gd: gd[1]))

            for game, plays in summary_set:
                print(f"- {YELLOW}{game}{DEFAULT}: {CYAN}{plays}{DEFAULT}")
        elif args.get('open'):
            webbrowser.open('https://boardgamegeek.com/collection/user/Nathansbud')               
        else:
            parser.print_help()
    else:
        choose_title()