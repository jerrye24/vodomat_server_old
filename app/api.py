from aiohttp import web
from models import get_status_by_number
from template_filters import datetime_from_timestamp_filter


async def status_by_number(request):
    number = request.match_info.get('number')
    try:
        number = int(number)
        async with request.app['db'].acquire() as conn:
            status_prev = await get_status_by_number(conn, number)
        status = {
            'datetime': datetime_from_timestamp_filter(status_prev['timestamp']),
            'low_water_balance': True if status_prev['water_balance'] < 50 else False,
            'error_water': True if status_prev['ev_water'] == 'СБОЙ' else False,
            'error_bill': True if status_prev['ev_bill'] == 'СБОЙ' else False,
            'error_volt': True if status_prev['ev_volt'] == 'СБОЙ' else False,
            'error_counter': True if status_prev['ev_counter_water'] == 'СБОЙ' else False,
            'error_register': True if status_prev['ev_register'] == 'СБОЙ' else False,
        }
        return web.json_response(status)
    except Exception as err:
        return web.json_response({'error': str(err)})