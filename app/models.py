from sqlalchemy import MetaData, Table, Column, func
from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.sql import select
import time

metadata = MetaData()

inbox_http = Table(
    'inbox_http', metadata,

    Column('id', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('text', String(48)),
    Column('processed', Integer)
)

avtomat = Table(
    'avtomat', metadata,

    Column('number', Integer, primary_key=True),
    Column('address', String(50)),
    Column('inv_num', Integer),
    Column('ph_number', String(13)),
    Column('driver', String(50)),
    Column('route', String(50)),
    Column('competitors', String(3))
)

status = Table(
    'status', metadata,

    Column('number', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('water_balance', Float),
    Column('how_money', Float),
    Column('water_price', Float),
    Column('ev_water', String(20)),
    Column('ev_bill', String(20)),
    Column('ev_volt', String(20)),
    Column('ev_counter_water', String(20)),
    Column('ev_register', String(20)),
    Column('time_to_block', Integer),
    Column('grn', Integer),
    Column('kop', Integer),
    Column('event', String(20)),
    Column('error', Integer)
)

avtomat_log_table = Table(
    'avtomat_log_table', metadata,

    Column('id', Integer, primary_key=True),
    Column('number', Integer),
    Column('water_balance', Float),
    Column('how_money', Float),
    Column('water_price', Float),
    Column('ev_water', String(6)),
    Column('ev_bill', String(6)),
    Column('ev_volt', String(6)),
    Column('ev_counter_water', String(6)),
    Column('ev_register', String(6)),
    Column('event', String(20)),
    Column('grn', String(4)),
    Column('kop', String(4)),
    Column('timestamp', Integer)
)

avtomat_coll_table = Table(
    'avtomat_coll_table', metadata,

    Column('id', Integer, primary_key=True),
    Column('number', Integer),
    Column('how_money', Float),
    Column('event', String(20)),
    Column('timestamp', Integer)
)


async def write_data_to_tables(conn, data_from_avtomat):
    query_get_avtomat = await conn.execute(avtomat.select().where(avtomat.c.number==data_from_avtomat['number']))
    current_avtomat = await query_get_avtomat.first()
    if not current_avtomat:
        await conn.execute(avtomat.insert().\
            values(number=data_from_avtomat['number'], address=f"New {data_from_avtomat['number']}",
                   inv_num=data_from_avtomat['number'], ph_number='',
                   driver='', route='', competitors='нет'))
    query_get_status = await conn.execute(status.select().where(status.c.number==data_from_avtomat['number']))
    current_status = await query_get_status.first()
    if not current_status:
        await conn.execute(status.insert().\
            values(number=data_from_avtomat['number'], timestamp=int(time.time()),
                   water_balance=data_from_avtomat['water_balance'],
                   how_money=data_from_avtomat['how_money'], water_price=data_from_avtomat['water_price'],
                   ev_water=data_from_avtomat['ev_water'], ev_bill=data_from_avtomat['ev_bill'],
                   ev_volt=data_from_avtomat['ev_volt'], ev_counter_water=data_from_avtomat['ev_counter_water'],
                   ev_register=data_from_avtomat['ev_register'], time_to_block=data_from_avtomat['time_to_block'],
                   grn=data_from_avtomat['grn'], kop=data_from_avtomat['kop'],
                   event=data_from_avtomat['event'], error=data_from_avtomat['error']))
    else:
        await conn.execute(status.update().where(status.c.number==data_from_avtomat['number']).\
            values(timestamp=int(time.time()), water_balance=data_from_avtomat['water_balance'],
                   how_money=data_from_avtomat['how_money'], water_price=data_from_avtomat['water_price'],
                   ev_water=data_from_avtomat['ev_water'], ev_bill=data_from_avtomat['ev_bill'],
                   ev_volt=data_from_avtomat['ev_volt'], ev_counter_water=data_from_avtomat['ev_counter_water'],
                   ev_register=data_from_avtomat['ev_register'], time_to_block=data_from_avtomat['time_to_block'],
                   grn=data_from_avtomat['grn'], kop=data_from_avtomat['kop'],
                   event=data_from_avtomat['event'], error=data_from_avtomat['error']))
    await conn.execute(avtomat_log_table.insert().\
        values(number=data_from_avtomat['number'], timestamp=int(time.time()),
               water_balance=data_from_avtomat['water_balance'],
               how_money=data_from_avtomat['how_money'], water_price=data_from_avtomat['water_price'],
               ev_water=data_from_avtomat['ev_water'], ev_bill=data_from_avtomat['ev_bill'],
               ev_volt=data_from_avtomat['ev_volt'], ev_counter_water=data_from_avtomat['ev_counter_water'],
               ev_register=data_from_avtomat['ev_register'], grn=data_from_avtomat['grn'],
               kop=data_from_avtomat['kop'], event=data_from_avtomat['event']))


async def write_collection(conn, data_from_avtomat):
    query = avtomat_coll_table.insert().values(number=data_from_avtomat['number'], how_money=data_from_avtomat['how_money'],
                                               event=data_from_avtomat['event'], timestamp=int(time.time()))
    await conn.execute(query)


async def write_line_to_inbox_http(conn, line):
    query = inbox_http.insert().values(timestamp=int(time.time()), text=line, processed=0)
    await conn.execute(query)
