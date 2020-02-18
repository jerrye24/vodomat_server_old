import yaml
import pathlib
import os

class Config:
    def __init__(self):
        self.mysql = {
            'database': os.environ.get('MYSQL_DATABASE'), 'user': os.environ.get('MYSQL_USER'),
            'password': os.environ.get('MYSQL_PASSWORD'), 'host': os.environ.get('MYSQL_HOST'),
            'port': int(os.environ.get('MYSQL_PORT'))
        }
        self.redis = {
            'host': os.environ.get('REDIS_HOST'), 'port': os.environ.get('REDIS_PORT')
        }
        self.SECRET_KEY = os.environ.get('SECRET_KEY')

config = Config()
BASE_DIR = pathlib.Path(__file__).parent
config_path = BASE_DIR / 'vodomat_server_old.yaml'

with open(config_path, 'w') as f:
    try:
        dump = yaml.dump(config, default_flow_style=False)
        f.write(dump.replace('!!', '#'))
    except Error as err:
        f.write(err)