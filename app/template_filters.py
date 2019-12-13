from datetime import datetime

def datetime_from_timestamp_filter(timestamp, format='%Y-%m-%d / %H:%M'):
    return datetime.fromtimestamp(timestamp).strftime(format)