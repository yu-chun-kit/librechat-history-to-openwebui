from datetime import datetime, timezone
import time

def convert_mongodb_time_to_epoch_seconds(mongo_time):
    """Converts MongoDB's ISODate object or string to Unix epoch seconds (integer)."""
    if isinstance(mongo_time, dict) and '$date' in mongo_time:
        ts_str = mongo_time['$date']
    elif isinstance(mongo_time, str):
        ts_str = mongo_time
    elif isinstance(mongo_time, datetime):
        if mongo_time.tzinfo is None:
            mongo_time = mongo_time.replace(tzinfo=timezone.utc)
        else:
            mongo_time = mongo_time.astimezone(timezone.utc)
        return int(mongo_time.timestamp())
    else:
        print(f"  Warning: Unrecognized time format: {mongo_time}, using current time.")
        return int(time.time())
    try:
        dt_object = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return int(dt_object.timestamp())
    except Exception as e:
        print(f"  Warning: Time conversion error for '{ts_str}': {e}, using current time.")
        return int(time.time())
