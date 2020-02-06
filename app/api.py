from aiohttp import web
from models import get_status_by_number, get_status_by_address
from template_filters import datetime_from_timestamp_filter


async def get_status(request):
    avtomat = request.match_info.get('avtomat')
    try:
        avtomat = int(avtomat)
    except:
        avtomat = avtomat
    try:
        async with request.app['db'].acquire() as conn:
            if isinstance(avtomat, int):
                status_prev = await get_status_by_number(conn, avtomat)
            if isinstance(avtomat, str):
                status_prev = await get_status_by_address(conn, avtomat)
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
