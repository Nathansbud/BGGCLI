import requests
import json
import os
import datetime
import xmltodict

bgg_api = "https://api.geekdo.com/xmlapi2"

def get_games(name):
    response = requests.get(f'{bgg_api}/search?query={name.replace(" ", "%20")}&exact=1&type=boardgame')
    if response:
        response = xmltodict.parse(response.content)
        total = int(response['items']['@total'])
        if total == 0: return []
        elif total == 1:
            item = response['items']['item']
            return [{'name': item['name']['@value'], 'year': item['yearpublished']['@value'], 'idx':item['@id']}]
        else:
            items = [{'name': item['name']['@value'], 'year': item['yearpublished']['@value'], 'idx':item['@id']} for item in response['items']['item']]
            return items
    return []

def log_play(gid, plays=1):
    with requests.Session() as session, open(os.path.join(os.path.dirname(__file__), "credentials", "bgg.json")) as jf:
        login = {"credentials": json.load(jf)}
        headers = {'content-type': 'application/json'}
        cookies = session.post('https://boardgamegeek.com/login/api/v1', data=json.dumps(login), headers=headers)
        playload = {
            "playdate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "objectid": f"{gid}",
            "objecttype":"thing",
            "action":"save",
            "quantity": f"{plays}",
        }

        response = session.post("https://boardgamegeek.com/geekplay.php", data=json.dumps(playload), headers=headers)
        #Still returns 200 on failure; check if "invalid action" appears in the returned html
        return not "invalid action" in response.text.lower()

if __name__ == '__main__':
    pass