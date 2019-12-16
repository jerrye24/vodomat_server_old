from datetime import datetime
import pytz

def datetime_from_timestamp_filter(timestamp, format='%Y-%m-%d / %H:%M'):
    tz = pytz.timezone('Europe/Kiev')
    return datetime.fromtimestamp(timestamp, tz=tz).strftime(format)