from aiohttp import web
import aioredis
from aiomysql.sa import create_engine
from views import index, get_data, status_of_avtomats, list_of_avtomats, update_avtomat
from views import list_of_users, delete_user, create_user, update_user
from views import login, logout
from settings import config
import argparse
import aiohttp_jinja2
from aiohttp_session import setup as setup_session
from aiohttp_session.redis_storage import RedisStorage
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy
from aiohttp_security import authorized_userid, permits
from db_auth import DBAuthorizationPolicy
import jinja2
import os
from template_filters import datetime_from_timestamp_filter
from middlewares import setup_middlewares
import aiojobs

parser = argparse.ArgumentParser(description='vodomat server old')
parser.add_argument('--port')
parser.add_argument('--path')

routes = [web.route('GET', '/', index, name='index'),
          web.route('GET', '/ufkc721.php', get_data),
          web.route('GET', '/status', status_of_avtomats, name='status_of_avtomats'),
          web.route('GET', '/avtomats', list_of_avtomats, name='list_of_avtomats'),
          web.route('POST', '/update_avtomat', update_avtomat, name='update_avtomat'),
          web.route('GET', '/users', list_of_users, name='list_of_users'),
          web.route('POST', '/create_user', create_user, name='create_user'),
          web.route('POST', '/update_user', update_user, name='update_user'),
          web.route('POST', '/delete_user', delete_user, name='delete_user'),
          web.route('GET', '/login', login, name='login'),
          web.route('POST', '/login', login, name='login'),
          web.route('GET', '/logout', logout, name='logout')
        ]

async def init_db(app):
    conf = app['config']['mysql']
    engine = await create_engine(
        db=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=1,
        maxsize=5,
        autocommit=True,
        charset='utf8',
    )
    app['db'] = engine
    return engine


async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()


async def init_db_redis(app):
    conf = app['config']['redis']
    redis = await aioredis.create_redis_pool((conf['host'], conf['port']), maxsize=5)
    app['db_redis'] = redis
    return redis


async def close_db_redis(app):
    app['db_redis'].close()
    await app['db_redis'].wait_closed()


async def current_user_context_processor(request):
    username = await authorized_userid(request)
    is_admin = await permits(request, '1')
    return {'current_user': {'username': username, 'is_admin': is_admin}}


async def make_app():
    app = web.Application()
    app['config'] = config
    app['session_name'] = 'VODOMAT_SESSION'
    app.on_startup.extend([init_db, init_db_redis])
    app.on_cleanup.extend([close_db, close_db_redis])
    app.add_routes(routes)

    db_pool = await init_db(app)
    redis_pool = await init_db_redis(app)

    setup_session(app, RedisStorage(redis_pool, cookie_name=app['session_name'], max_age=3600))
    setup_security(app, SessionIdentityPolicy(), DBAuthorizationPolicy(db_pool))

    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('{}/templates'.format(os.path.dirname(__file__))),
                         filters={'datetime_from_timestamp': datetime_from_timestamp_filter},
                         context_processors=[current_user_context_processor],
                         )
    setup_middlewares(app)

    aiojobs.aiohttp.setup(app)

    return app

if __name__ == '__main__':
    args = parser.parse_args()
    web.run_app(make_app(), port=args.port, path=args.path)
