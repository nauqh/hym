import yaml


class Config:
    def __init__(self, path: str):
        with open(path, 'r') as file:
            config = yaml.safe_load(file)

        players = config['players']
        self.puuids = set(players.values())
        self.TOKEN = config['TOKEN']
        self.GUILD = config['GUILD']
        self.stdout_channel_id = config['STDOUT_CHANNEL_ID']
        self.LEAGUE_CHANNEL_ID = config['LEAGUE_CHANNEL_ID']
