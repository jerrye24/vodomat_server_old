from sqlalchemy import create_engine, MetaData

from app.settings import config
from app.models import inbox_http, avtomat, status, avtomat_log_table, avtomat_coll_table

DSN = "mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

def create_tables(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[inbox_http, avtomat, status, avtomat_log_table, avtomat_coll_table])


if __name__ == '__main__':
    db_url = DSN.format(**config['mysql'])
    engine = create_engine(db_url)

    create_tables(engine)