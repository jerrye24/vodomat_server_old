from aiohttp import web
import time
import aiohttp_jinja2
import models
from forms import validate_update_avtomat_form, validate_create_user_form, validate_update_user_form, validate_login_form
from aiohttp_security import authorized_userid, remember, check_permission
from aiohttp_session import get_session
from security import redirect_to_login
from aiojobs.aiohttp import atomic


def get_event(number_of_event):
    events = {
        1: 'Нет воды',
        2: 'Нет электричества',
        3: 'Инкассация',
        4: 'Удар',
        5: 'Мало воды',
        6: 'Ответ на запрос',
        7: 'Купюроприемник',
        8: 'Регистратор',
        9: 'Включение или перезапуск',
        10: 'Вкл. сервисный',
        11: 'Выкл. сервисный',
        12: 'Вскрытие',
        13: '12 часов',
    }
    return events.get(number_of_event, number_of_event)


def get_error(error):
    errors = {
        0: 'НОРМА',
        1: 'СБОЙ'
    }
    return errors.get(error, 'error')


def parsing_line(line):
    data = dict()
    data['number'] = int(line[0:4])
    data['timestamp'] = time.time()
    data['how_money'] = float(line[14:20]) / 100
    data['water_balance'] = float(line[20:26]) / 100
    data['water_price'] = float(line[26:30]) / 100
    data['ev_water'] = get_error(int(line[40]))
    data['ev_bill'] = get_error(int(line[42]))
    data['ev_volt'] = get_error(int(line[41]))
    data['ev_counter_water'] = get_error(int(line[43]))
    data['ev_register'] = get_error(int(line[44]))
    data['time_to_block'] = int(line[30:32])
    data['grn'] = int(line[32:36])
    data['kop'] = int(line[36:40])
    data['event'] = get_event(int(line[46:48]))
    data['error'] = 0 if any([int(line[40]), int(line[42]), int(line[41]), int(line[43]), int(line[44])]) else 1
    return data


@redirect_to_login
async def index(request):
    location = request.app.router['status_of_avtomats'].url_for()
    response = web.HTTPFound(location=location)
    return response


@atomic
async def get_data(request):
    line = request.rel_url.query.get('data', default='')
    if len(line) == 48:
        async with request.app['db'].acquire() as conn:
            try:
                # Parsing and write data from avtomat
                data_from_avtomat = parsing_line(line)
                price = await models.write_data_to_tables(conn, data_from_avtomat)
                # Write data in collection table
                if data_from_avtomat['event'] == 'Инкассация':
                    await models.write_collection(conn, data_from_avtomat)
                # Change water price in avtomat
                if price:
                    await models.discard_avtomat_price(conn, data_from_avtomat['number'])
                    return web.Response(text=f'\nPrice={price:04d}\n')
                return web.Response(text='ok')
            except:
                # If line with some errors
                await models.write_line_to_inbox_http(conn, line)
                return web.Response(text='error')
    else:
        return web.Response(text='500')


@aiohttp_jinja2.template('status_of_avtomats.j2')
@redirect_to_login
async def status_of_avtomats(request):
    async with request.app['db'].acquire() as conn:
        statuses = await models.get_statuses(conn)
    return {'statuses': statuses}


@aiohttp_jinja2.template('list_of_avtomats.j2')
@redirect_to_login
async def list_of_avtomats(request):
    async with request.app['db'].acquire() as conn:
        avtomats = await models.get_avtomats(conn)
    return {'avtomats': avtomats}


@redirect_to_login
async def update_avtomat(request):
    location = request.app.router['list_of_avtomats'].url_for()
    response = web.HTTPFound(location=location)
    if request.method == 'POST':
        form = await request.post()
        async with request.app['db'].acquire() as conn:
            error = await validate_update_avtomat_form(conn, form)
            if error:
                pass
    return response



@aiohttp_jinja2.template('list_of_users.j2')
@redirect_to_login
async def list_of_users(request):
    await check_permission(request, '1')
    async with request.app['db'].acquire() as conn:
        users = await models.get_users(conn)
    return {'users': users}


@redirect_to_login
async def create_user(request):
    await check_permission(request, '1')
    location = request.app.router['list_of_users'].url_for()
    response = web.HTTPFound(location=location)
    if request.method == 'POST':
        form = await request.post()
        async with request.app['db'].acquire() as conn:
            error = await validate_create_user_form(conn, form)
            if error:
                pass
    return response


@redirect_to_login
async def update_user(request):
    await check_permission(request, '1')
    location = request.app.router['list_of_users'].url_for()
    response = web.HTTPFound(location=location)
    if request.method == 'POST':
        form = await request.post()
        async with request.app['db'].acquire() as conn:
            error = await validate_update_user_form(conn, form)
            if error:
                pass
    return response


@redirect_to_login
async def delete_user(request):
    await check_permission(request, '1')
    location = request.app.router['list_of_users'].url_for()
    response = web.HTTPFound(location=location)
    if request.method == 'POST':
        form = await request.post()
        user_id = form.get('user_id')
        async with request.app['db'].acquire() as conn:
            await models.delete_user(conn, user_id)
    return response


@aiohttp_jinja2.template('login.j2')
async def login(request):
    username = await authorized_userid(request)
    if username:
        location = request.app.router['status_of_avtomats'].url_for()
        raise web.HTTPFound(location=location)
    if request.method == 'POST':
        form = await request.post()
        async with request.app['db'].acquire() as conn:
            error = await validate_login_form(conn, form)
            if error:
                return {'error': error}
            else:
                location = request.app.router['status_of_avtomats'].url_for()
                response = web.HTTPFound(location=location)
                user = await models.get_user_by_name(conn, form.get('username'))
                await remember(request, response, user['username'])
                raise response
    return {}


async def logout(request):
    location = request.app.router['login'].url_for()
    response = web.HTTPFound(location=location)
    session = await get_session(request)
    if session:
        session_key = request.app['session_name'] + '_' + session.identity
        with (await request.app['db_redis']) as redis_pool:
            await redis_pool.execute('del', session_key)
    return response
