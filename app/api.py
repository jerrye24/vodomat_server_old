from aiohttp import web
import models
from template_filters import datetime_from_timestamp_filter
import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from forms import validate_login_form
import models

# API KEY ----------------------------------------------------------------------------------
async def generate_api_key(secret_key, username, expiration=3600):
    s = Serializer(secret_key, expires_in=expiration)
    return s.dumps({'username': username})


async def get_api_key(request):
    form = request.rel_url.query
    async with request.app['db'].acquire() as conn:
        error = await validate_login_form(conn, form)
        if error:
            return web.json_response({'error': error}, status=400)
        else:
            secret_key = request.app['config']['SECRET_KEY']
            username = form['username']
            user = await models.get_user_by_name(conn, username)
            city = user.get('city')
            api_key = await generate_api_key(secret_key, username)
        return web.json_response({'api_key': api_key.decode('utf8'), 'city': city})


async def verify_api_key(request, api_key):
    secret_key = request.app['config']['SECRET_KEY']
    s = Serializer(secret_key)
    try:
        data = s.loads(api_key)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    async with request.app['db'].acquire() as conn:
        user = await models.get_user_by_name(conn, data['username'])
    if not user:
        return False
    else:
        return True


def check_api_key_decorator(func):
    async def wrapper(request):
        try:
            api_key = request.headers['HTTP-X-API-KEY']
        except KeyError:
            return web.Response(text='500')
        verified = await verify_api_key(request, api_key)
        if not verified:
            return web.json_response({'error': 'wrong api key'}, status=400)
        else:
            return await func(request)
    return wrapper


#  For Telegram ----------------------------------------------------------------------------
replace_street = {
    'гвардейцев': 'Гв.',
    'богдана': 'Б. Хмельницкого',
    'большая': 'Б.',
    'броненосца': 'Б. Потемкина',
    'отакара': 'От.',
    'людвига': 'Л. Свободы',
    'луи': 'Л. Пастера',
    'академика': 'Ак.',
    'дружбы': 'Др.',
    'франтишека': 'Ф.',
    'натальи': 'Ужвий',
}


async def check_street(street):
    new_street = replace_street.get(street.lower(), street.capitalize())
    return new_street


async def get_avtomat_from_message(message):
    try:
        avtomat = int(message)
        return avtomat
    except:
        split_address = message.split()
        street = await check_street(split_address[0])
        house = split_address[-1]
        avtomat = f'{street}%{house}%'
        return avtomat


async def get_status(request):
    number_or_address = request.match_info.get('avtomat')
    avtomat = await get_avtomat_from_message(number_or_address)
    try:
        async with request.app['db'].acquire() as conn:
            if isinstance(avtomat, int):
                status_prev = await models.get_status_by_number(conn, avtomat)
            if isinstance(avtomat, str):
                status_prev = await models.get_status_by_address(conn, avtomat)
            if not status_prev:
                return web.json_response({'error': 'Автомат не найден'}, status=400)
            status = {
                'datetime': datetime_from_timestamp_filter(status_prev.get('timestamp')),
                'low_water_balance': True if status_prev.get('water_balance') < 50 else False,
                'error_water': True if status_prev.get('ev_water') == 'СБОЙ' else False,
                'error_bill': True if status_prev.get('ev_bill') == 'СБОЙ' else False,
                'error_volt': True if status_prev.get('ev_volt') == 'СБОЙ' else False,
                'error_counter': True if status_prev.get('ev_counter_water') == 'СБОЙ' else False,
                'error_register': True if status_prev.get('ev_register') == 'СБОЙ' else False,
            }
            return web.json_response(status)
    except Exception as err:
        return web.json_response({'error': str(err)}, status=400)
#  --------------------------------------------------------------------------------------------


@check_api_key_decorator
async def get_statuses_by_city(request):
    city = request.match_info.get('city').capitalize()
    try:
        async with request.app['db'].acquire() as conn:
            statuses = await models.get_statuses_by_city(conn, city)
            statuses_to_show = [{
                'number': status.get('number'),
                'address': status.get('address'),
                'datetime': datetime_from_timestamp_filter(status.get('timestamp')),
                'water': status.get('water_balance'),
                'money': status.get('how_money'),
                'price': status.get('water_price'),
                'low_water_balance': True if status.get('water_balance') < 50 else False,
                'error_water': True if status.get('ev_water') == 'СБОЙ' else False,
                'error_bill': True if status.get('ev_bill') == 'СБОЙ' else False,
                'error_volt': True if status.get('ev_volt') == 'СБОЙ' else False,
                'error_counter': True if status.get('ev_counter_water') == 'СБОЙ' else False,
                'error_register': True if status.get('ev_register') == 'СБОЙ' else False,
            } for status in statuses]
            return web.json_response(statuses_to_show)
    except Exception as err:
        return web.json_response({'error': str(err)}, status=400)


@check_api_key_decorator
async def get_statistic(request):
    number = request.rel_url.query.get('number')
    date = request.rel_url.query.get('date')
    if not number:
        return web.json_response({'error': 'number is required'})
    if not date:
        date = datetime.date.today().strftime('%Y-%m-%d')
    try:
        async with request.app['db'].acquire() as conn:
            statistic = await models.get_statistic(conn, number, date)
        statistic_to_show = [{
            'datetime': datetime_from_timestamp_filter(line.get('timestamp')),
            'water': line.get('water_balance'),
            'money': line.get('how_money'),
            'price': line.get('water_price'),
            'grn': int(line.get('grn')),
            'kop': int(line.get('kop')),
            'error_water': True if line.get('ev_water') == 'СБОЙ' else False,
            'error_bill': True if line.get('ev_bill') == 'СБОЙ' else False,
            'error_volt': True if line.get('ev_volt') == 'СБОЙ' else False,
            'error_counter': True if line.get('ev_counter_water') == 'СБОЙ' else False,
            'error_register': True if line.get('ev_register') == 'СБОЙ' else False,
            'event': line.get('event')
        } for line in statistic]
        return web.json_response(statistic_to_show)
    except Exception as err:
        return web.json_response({'error': str(err)}, status=400)
