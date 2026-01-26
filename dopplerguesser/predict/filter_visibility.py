from dopplerguesser.predict.observer import Observer
from dopplerguesser.predict.satellite import Satellite
import datetime as dt
from skyfield.api import load


def filter_visibility(observer: Observer, t: float, min_elevation: float, satellites: list[Satellite]):
    ts = load.timescale()

    t_sf = ts.from_datetime(dt.fromtimestamp(t, dt.datetime.timezone.utc))

    observer_gcrs = observer.location.at(t_sf)
    visible_satellites = []

    for sat in satellites:
        sat_gcrs = sat.satellite.at(t_sf)
        difference = sat_gcrs - observer_gcrs
        alt, _, _ = difference.altaz()

        if alt.degrees > min_elevation:
            visible_satellites.append(sat)

    return visible_satellites
