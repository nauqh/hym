import requests
import time
import pandas as pd


class RiotAPI:
    def __init__(self, token):
        self.token = token

    def _make_request(self, url):
        while True:
            resp = requests.get(url)
            if resp.status_code == 429:
                print("Rate limit hit, sleeping for 10 seconds")
                time.sleep(10)
            elif resp.status_code == 404:
                print("Summoner not found")
                return
            else:
                resp.raise_for_status()
                return resp.json()

    def get_puuid(self, summoner, tagline) -> str:
        url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner}/{tagline}?api_key={self.token}"
        resp = self._make_request(url)
        return resp['puuid']

    def get_info(self, puuid, region) -> dict:
        url = f"https://{region.lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={self.token}"
        resp = self._make_request(url)

        url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}?api_key={self.token}"
        resp2 = self._make_request(url)
        resp = {**resp, **resp2}
        return resp

    def get_rank(self, summoner_id, region) -> list:
        url = f"https://{region.lower()}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={self.token}"
        resp = self._make_request(url)
        return resp

    def get_match_ids(self, puuid, no_games, queue_id) -> list:
        url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={no_games}&queue={queue_id}&api_key={self.token}"
        resp = self._make_request(url)
        return resp

    def get_match_data(self, match_id) -> dict:
        url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={self.token}"
        match_data = self._make_request(url)
        return match_data

    def find_player_data(self, match_data, puuid):
        participants = match_data['metadata']['participants']
        player_index = participants.index(puuid)
        player_data = match_data['info']['participants'][player_index]
        player_data['matchId'] = match_data['metadata']['matchId']
        player_data['info'] = match_data['info']
        return player_data


def load_data(puuids: set) -> pd.DataFrame:

    df = pd.read_csv('app/data/50games.csv')

    def get_focus_matches(df: pd.DataFrame, puuids: set) -> pd.DataFrame:
        """
        Find matches that all players in puuids participate.
        """
        puuids_by_match = df.groupby(
            'matchId')['puuid'].apply(set).reset_index()
        focus_matches = puuids_by_match[puuids_by_match['puuid']
                                        == puuids]['matchId']
        return df[df['matchId'].isin(focus_matches)]

    df['riotIdGameName'] = df['puuid'].map({
        '8UIhStkspIglog9paowA4mXzlckT-xySwWNIFac3o2ojumva9ffkFMda_jGpW_hhInKWpvUp5pPPrA': 'tuandao1311',
        'mh3B8Naz1MbJ6RE7dJTu3ZCLh7Rwo6CCJQiA-fVlLXUuQmkibMVMztpCLALJMMJQm4QOevN1-u0lnA': 'cozybearrrrr',
        'DV0Aad31H16g3lItoojolWMPZQYOj0l90KzVSUV-qF3QlF92hOC_WLLssdR1MqPS-3UMEKp0Mn5woA': 'tuanancom',
        'aTa5_43m0w8crNsi-i9nxGpSVU06WZBuK-h9bZEOK0g_lJox3XF4Dv4BzVwZieRj0QwlGnJ4SZbftg': 'nauqh',
        'idASdW5eSrO5Oih-ViK07RdeXE33JM1Mm3FwV7JiveTwbqfjl1vQUvToJ95c1B4EeQd8BAZgXkGSUw': 'wavepin'
    })

    df_focus = get_focus_matches(df, puuids)
    return df_focus


def calculate_wins_loses(df):
    wins = df.groupby('matchId')['win'].max().sum()
    totals = df['matchId'].nunique()
    loses = totals - wins
    return wins, loses, totals


def get_champ_winrate(champion, df):
    champion_df = df[df['championName'] == champion]
    winrate = champion_df['win'].mean() * 100
    return winrate


def get_champ_kda(champion, df):
    champion_df = df[df['championName'] == champion]
    kills = champion_df['kills'].mean()
    deaths = champion_df['deaths'].mean()
    assists = champion_df['assists'].mean()
    return kills, deaths, assists


def get_team_participation_stats(df: pd.DataFrame):
    cols = ['kills', 'deaths', 'assists', 'challenges.killParticipation']
    agg_dict = {
        col: (col, 'sum') if col != 'challenges.killParticipation'
        else (col, lambda x: x.mean() * 100)
        for col in cols
    }

    stats = df.groupby('riotIdGameName').agg(**agg_dict).reset_index()

    return stats


def get_team_early_game_stats(df: pd.DataFrame):
    stats = df.groupby('riotIdGameName')[[
        'firstBloodKill',
        'firstBloodAssist',
        'firstTowerKill',
        'firstTowerAssist'
    ]].sum().reset_index()

    return stats


def get_team_combat_stats(df: pd.DataFrame):
    stats = df.groupby('riotIdGameName')[[
        'totalDamageDealtToChampions',
        'totalDamageTaken',
        'totalHealsOnTeammates',
        'goldEarned'
    ]].mean().reset_index()

    return stats


def get_team_damage_proportion(df: pd.DataFrame):
    stats = df.groupby('riotIdGameName')[[
        'physicalDamageDealtToChampions',
        'magicDamageDealtToChampions',
        'trueDamageDealtToChampions'
    ]].mean().reset_index()

    return stats


if __name__ == "__main__":
    api = RiotAPI('RGAPI-a384a673-d288-42ec-a860-55a1602dba94')
    s = api.get_info(
        '8UIhStkspIglog9paowA4mXzlckT-xySwWNIFac3o2ojumva9ffkFMda_jGpW_hhInKWpvUp5pPPrA', 'vn2')
    print(s)
