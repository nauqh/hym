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

    df = pd.read_csv('app/data/100games.csv')

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
    df_focus['date'] = pd.to_datetime(
        df_focus['info.gameStartTimestamp'], unit='ms')
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


def calculate_roles_winrate(df):
    # Aggregate and format most used champion with usage count, calculate win rate, average damage, and damage rank
    most_used_champion_stats = (
        df.groupby(['riotIdGameName', 'championName'])
        .agg(
            usage_count=('championName', 'size'),
            winrate=('win', lambda x: (x == 1).mean() * 100),
            damage_rank=('damage_rank', 'mean')
        )
        .sort_values(['riotIdGameName', 'usage_count'], ascending=[True, False])
        .reset_index()
    )

    # Combine champion name and usage count into one column
    most_used_champion_stats['Most Used Champion'] = most_used_champion_stats['championName'] + \
        ' (' + most_used_champion_stats['usage_count'].astype(str) + ')'

    # Keep only the relevant columns and drop duplicates to get the most used champion per riotIdGameName
    most_used_champion_stats = most_used_champion_stats.drop_duplicates(subset=['riotIdGameName'])[
        ['riotIdGameName', 'Most Used Champion', 'winrate', 'damage_rank']
    ]

    # Step 2: Calculate the most appearing roles for each riotIdGameName
    df_roles = (
        df.groupby('riotIdGameName')
        .agg(
            most_appearing_roles=('assigned_roles', lambda roles: ', '.join(
                pd.Series([role for sublist in roles for role in sublist])
                .value_counts()
                .nlargest(2)  # Get the top 2 roles by frequency
                .index.tolist()
            ))
        )
        .reset_index()
    )

    # Step 3: Merge both results to get a single combined table
    combined_result = most_used_champion_stats.merge(
        df_roles, on='riotIdGameName')

    # Rename columns for clarity
    combined_result = combined_result.rename(columns={
        'riotIdGameName': 'Summoner',
        'winrate': 'Win Rate (%)',
        'damage_rank': 'Damage Rank',
        'most_appearing_roles': 'Roles'
    })

    # Format the final combined result
    combined_result['Win Rate (%)'] = combined_result['Win Rate (%)'].astype(
        int)
    combined_result['Damage Rank'] = combined_result['Damage Rank'].apply(
        lambda x: f"{x:,.1f}")

    return combined_result


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


def get_summoner_stats(df: pd.DataFrame, name: str):
    cols = ['kills', 'deaths', 'assists', 'totalDamageDealtToChampions', 'pentaKills',
            'totalMinionsKilled', 'totalTimeCCDealt', 'longestTimeSpentLiving']
    agg_dict = {col: (col, 'sum') if col in ('pentaKills')
                else (col, 'mean') for col in cols}
    stats = df.groupby('riotIdGameName').agg(**agg_dict).reset_index()
    return stats[stats['riotIdGameName'] == name].to_dict(orient='records')[0]


if __name__ == "__main__":
    api = RiotAPI('RGAPI-a384a673-d288-42ec-a860-55a1602dba94')
    s = api.get_info(
        '8UIhStkspIglog9paowA4mXzlckT-xySwWNIFac3o2ojumva9ffkFMda_jGpW_hhInKWpvUp5pPPrA', 'vn2')
    print(s)
