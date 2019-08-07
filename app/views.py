from aiohttp import web
import models


def get_event(number_of_event):
    events = {
        1: 'нет воды',
        2: 'электропитание',
        3: 'инкассация',
        4: 'удар',
        5: 'мало воды',
        6: 'отправка данных',
        7: 'купюроприемник',
        8: 'регистратор',
        9: 'перезапуск',
        10: 'сервисный режим вкл',
        11: 'сервисный режим выкл',
        12: 'сервисное вскрытие',
        13: '12 часов',
    }
    return events.get(number_of_event)


def parsing_line(line):
    data = {}
    data['number'] = int(line[0:4])
    data['how_money'] = float(line[14:20]) / 100
    data['water_balance'] = float(line[20:26]) / 100
    data['water_price'] = float(line[26:30]) / 100
    data['ev_water'] = int(line[40])
    data['ev_bill'] = int(line[42])
    data['ev_volt'] = int(line[41])
    data['ev_counter_water'] = int(line[43])
    data['ev_register'] = int(line[44])
    data['time_to_block'] = int(line[30:32])
    data['grn'] = int(line[32:36])
    data['kop'] = int(line[36:40])
    data['event'] = get_event(int(line[46:48]))
    return data
    

async def index(request):
    return web.Response(text='500')


async def get_data(request):
    line = request.rel_url.query.get('data', dafault='')
    if len(data) == 48:
        async with request.app['db'].acquire() as conn:
            try:
                data_from_avtomat = parsing_line(line)
                await models.write_data_to_tables(conn, data_from_avtomat)
                if data_from_avtomat['event'] == 'инкассация':
                    await models.write_collection(conn, data_from_avtomat)
                return web.Response(text='ok')
            except:
                await models.write_line_to_inbox_http(conn, line)
                return web.Response(text='error')
    else:
        return web.Respone(text='500')

