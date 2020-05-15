# Set path to correct packages import (CHANGE IT!)
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute() / 'app'))

import pytest
import time
from app.views import *


@pytest.mark.parametrize('f,l,expected',
    [
        pytest.param(
            0, 0, {'ev_water': 'НОРМА',
                   'ev_volt': 'НОРМА',
                   'ev_bill': 'НОРМА',
                   'ev_counter_water': 'НОРМА',
                   'ev_register': 'НОРМА'}, id='all work'
        ),
        pytest.param(
            1, 0, {'ev_water': 'СБОЙ',
                   'ev_volt': 'НОРМА',
                   'ev_bill': 'НОРМА',
                   'ev_counter_water': 'НОРМА',
                   'ev_register': 'НОРМА'}, id='ev_water fail'
        ),
        pytest.param(
            0, 1, {'ev_water': 'НОРМА',
                   'ev_volt': 'НОРМА',
                   'ev_bill': 'НОРМА',
                   'ev_counter_water': 'СБОЙ',
                   'ev_register': 'НОРМА'}, id='ev_counter_water fail'
        ),
        pytest.param(
            8, 0, {'ev_water': 'error',
                   'ev_volt': 'error',
                   'ev_bill': 'error',
                   'ev_counter_water': 'НОРМА',
                   'ev_register': 'НОРМА'}, id='not allowed value in flag'
        ),
    ]
)
def test_water_machine_nodes_health_status(f, l, expected):
    assert water_machine_nodes_health_status(dict(), f, l) == expected


@pytest.mark.parametrize('flag,expected', [(0, 'НОРМА'), (1, 'СБОЙ')])
def test_get_error(flag, expected):
    assert get_error(flag) == expected


@pytest.mark.parametrize('event,expected', [(1, 'Нет воды'), (20, '20')])
def test_get_event(event, expected):
    for i in range(20):
        assert len(get_event(i)) < 20, 'Len of event can not be more 20 symbols (only for old server)'
    assert get_event(event) == expected


@pytest.mark.parametrize('line,expected',
    [
        pytest.param(
            '000100000000002222223333330127445555666610110006',
            {'number': 1,
             'how_money': 222222 / 100,
             'water_balance': 333333 / 100,
             'water_price': 127 / 100,
             'ev_water': 'СБОЙ',
             'ev_bill': 'СБОЙ',
             'ev_volt': 'НОРМА',
             'ev_counter_water': 'СБОЙ',
             'ev_register': 'НОРМА',
             'time_to_block': 44,
             'grn': 5555,
             'kop': 6666,
             'event': 'Ответ на запрос',
             'error': 0},
             id='right parsing'
        ),
    ]
)
async def test_parsing_line_48(line, expected):
    assert len(line) == 48, 'Len of line must be only 48 symbols'
    data = await parsing_line_48(line)
    timestamp = time.time()
    data['timestamp'] = timestamp
    expected['timestamp'] = timestamp
    assert data == expected, 'Wrong parsing of 48-line'


@pytest.mark.parametrize('line,expected',
    [
        pytest.param(
            '000100000000002222223333330127445555666677777788990011000006',
            {'number': 1,
             'how_money': 222222 / 100,
             'water_balance': 333333 / 100,
             'water_price': 127 / 100,
             'time_to_block': 44,
             'grn': 5555,
             'kop': 6666,
             'money_app': 777777,
             'bill_not_work': 88,
             'coin_not_work': 99,
             'ev_water': 'СБОЙ',
             'ev_volt': 'НОРМА',
             'ev_bill': 'НОРМА',
             'ev_counter_water': 'СБОЙ',
             'ev_register': 'НОРМА',
             'event': 'Ответ на запрос',
             'error': 0},
             id='right parsing'
        ),
    ]
)
async def test_parsing_line_60(line, expected):
    assert len(line) == 60, 'Len of line must be only 60 symbols'
    data = await parsing_line_60(line)
    timestamp = time.time()
    data['timestamp'] = timestamp
    expected['timestamp'] = timestamp
    assert data == expected, 'Wrong parsing of 60-line'
