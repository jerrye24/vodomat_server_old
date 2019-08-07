from aiohttp import web
from aiomysql.sa import create_engine
from views import index, get_data
from settings import config
import argparse

parser = argparse.ArgumentParser(description='vodomat server old')
parser.add_argument('--port')
parser.add_argument('--path')
routes = [web.get('/', index), web.get('/ufkc721.php', get_data)]


async def init_db(app):
    conf = app['config']['mysql']
    engine = await create_engine(
        db=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        autocommit=True,
    )
    app['db'] = engine


async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()


async def make_app():
    app = web.Application()
    app['config'] = config
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)
    app.add_routes(routes)

    return app


if __name__ == '__main__':
    args = parser.parse_args()
    web.run_app(make_app(), port=args.port, path=args.path)