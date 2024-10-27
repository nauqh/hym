import yaml


class Config:
    def __init__(self):
        with open('app/data/settings.yml', 'r') as file:
            config = yaml.safe_load(file)

        self.players = config['players']
        self.puuids = set(self.players.values())
        self.TOKEN = config['TOKEN']
        self.region = 'vn2'
