import requests
import time
from bs4 import BeautifulSoup
from mwclient import Site

site = Site("lol.fandom.com", path = "/")

def riot_api_request(url):
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            return response
        elif response.status_code == 429 or response.status_code == 500:
            time.sleep(10)
        else:
            raise Exception(f'Error during the request: {response.status_code}')

def leaguepedia_api_request(payload):
    print(f"Fetching data from tables : {payload['tables']}")
    total_response = []
    length = 500
    payload["offset"] = 0
    while length == 500:
        response = site.api(**payload)["cargoquery"]
        total_response += response
        length = len(response)
        if length == 500:
            payload["offset"] += 500
    print(f"Total fetched rows : {len(total_response)}")
    return total_response

def get_games(leagues = None, oldest_date = None):

    if leagues is not None:
        where_leagues = " AND T.League IN (" + ", ".join("'" + league + "'" for league in leagues) + ")"
    else:
        where_leagues = ""
    
    if oldest_date is not None:
        where_date = " AND SG.DateTime_UTC > '" + oldest_date + "'"
    else:
        where_date = ""

    payload = {
        "action" : "cargoquery",
        "limit" : "max",
        "tables" : "ScoreboardGames=SG, PostgameJsonMetadata=PJM, Tournaments=T, MatchSchedule=MS, MatchScheduleGame=MSG",
        "fields" : "SG.OverviewPage, SG.RiotPlatformGameId, T.League, T.Name, SG.Team1, SG.Team2, SG.DateTime_UTC, SG.Patch, MSG.RiotVersion, MS.BestOf, MSG.N_GameInMatch",
        "where" : f"SG.Patch LIKE '14.%'" + where_leagues + where_date,
        "order_by" : "SG.DateTime_UTC DESC",
        "join_on" : "SG.RiotPlatformGameId = PJM.RiotPlatformGameId, T.OverviewPage = SG.OverviewPage, SG.MatchId = MS.MatchId, SG.GameId = MSG.GameId",
    }
    return leaguepedia_api_request(payload)

def get_leagues():
    payload = {
        "action" : "cargoquery",
        "limit" : "max",
        "tables" : "Leagues=L",
        "fields" : "L.League, L.League_Short, L.Region",
    }
    return leaguepedia_api_request(payload)

if __name__ == '__main__':
    import pandas as pd
    leagues = pd.read_csv('data/all_leagues.csv', index_col = None)
    games = get_games(leagues['League'].values)
    df = pd.DataFrame.from_dict([item["title"] for item in games])
    df = df.rename(columns = {'Name' : 'Tournament'})
    df = df.drop(columns = ['DateTime UTC__precision'])
    df.to_csv('data/all_games.csv', index = None)