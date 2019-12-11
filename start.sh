#!/bin/sh

python create_config.py
python init_db.py

exec python app/main.py --port=808$APP_PORT