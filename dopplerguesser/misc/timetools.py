from skyfield.api import load
from skyfield.timelib import Timescale
from datetime import datetime, timezone

ts = load.timescale()


def unix_to_skyfield(unix_time):
    datetime_obj = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    return Timescale.from_datetime(ts, datetime_obj)
