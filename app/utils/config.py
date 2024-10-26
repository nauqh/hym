import yaml


class Config:
    def __init__(self):
        with open('app/data/settings.yml', 'r') as file:
            config = yaml.safe_load(file)

        players = config['players']
        self.puuids = set(players.values())
        self.TOKEN = config['TOKEN']
        self.region = 'vn2'
