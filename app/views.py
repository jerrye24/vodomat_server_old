from aiohttp import web
import models


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


async def index(request):
    return web.Response(text='500')


async def get_data(request):
    line = request.rel_url.query.get('data', default='')
    if len(line) == 48:
        async with request.app['db'].acquire() as conn:
            try:
                data_from_avtomat = parsing_line(line)
                await models.write_data_to_tables(conn, data_from_avtomat)
                if data_from_avtomat['event'] == 'Инкассация':
                    await models.write_collection(conn, data_from_avtomat)
                return web.Response(text='ok')
            except:
                await models.write_line_to_inbox_http(conn, line)
                return web.Response(text='error')
    else:
        return web.Response(text='500')


# API V1 -------------------------------------------------------------------------------------------------
async def list_statuses(request):
    if request.method == 'GET':
        async with request.app['db'].acquire() as conn:
            statuses = await models.get_statuses(conn)
        statuses_to_show = [dict(s) for s in statuses]
        number = request.rel_url.query.get('number')
        if number:
            statuses_to_show = [dict(s) for s in statuses_to_show if int(number) == s['number']]
        from_status = request.rel_url.query.get('from')
        to_status = request.rel_url.query.get('to')
        if from_status and to_status:
            from_status = int(from_status)
            to_status = int(to_status)
            statuses_to_show = statuses_to_show[from_status:to_status]
        fields = request.rel_url.query.get('fields')
        if fields:
            fields = fields.split(',')
            statuses_to_show = [{k: v for k, v in s.items() if k in fields} for s in statuses_to_show]
        return web.json_response(statuses_to_show)
