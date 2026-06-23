import numpy as np
import re
from dopplerguesser.misc.constants import C
from dopplerguesser.predict.observer import Observer
from dopplerguesser.predict.satellite import Satellite
from dopplerguesser.misc.timetools import unix_to_skyfield
from datetime import datetime, timezone


def _extract_epoch_jd_from_tle(tle_line1: str) -> float:
    epoch_str = tle_line1[18:32]
    year = int(epoch_str[0:2])
    day_of_year = float(epoch_str[2:14])

    if year < 57:
        year += 2000
    else:
        year += 1900

    y = year - 1
    a = y // 100
    b = 2 - a + a // 4

    jd0 = int(365.25 * (y + 4716)) + int(30.6001 * 14) + 1 + b - 1524.5
    jd = jd0 + day_of_year
    
    return jd


def filter_debris(satellites: list[Satellite]):
    exp = re.compile(r'\b(?:deb|r/?b)\b', re.IGNORECASE)
    filtered = []
    for sat in satellites:
        name_lower = sat.name.lower()
        if exp.search(name_lower):
            continue
        filtered.append(sat)
    return filtered


def filter_by_epoch(satellites: list[Satellite], maxage=14):
    """Filter satellites by TLE epoch age using efficient Julian date comparison."""
    now = datetime.now(tz=timezone.utc)
    year = now.year
    month = now.month
    day = now.day + now.hour / 24.0 + now.minute / 1440.0 + now.second / 86400.0
    
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd_now = jdn - 0.5
    
    max_age_jd = maxage
    
    filtered = []
    for sat in satellites:
        jd_epoch = _extract_epoch_jd_from_tle(sat.tle_line1)
        age_jd = abs(jd_now - jd_epoch)
        if age_jd <= max_age_jd:
            filtered.append(sat)
    
    return filtered


def filter_visibility(satellites: list[Satellite], observer: Observer, t, min_elevation=0.0):
    visible_satellites = []
    t_sf = unix_to_skyfield(t)

    observer_gcrs = observer.location.at(t_sf)

    for sat in satellites:
        difference = sat.satellite.at(t_sf) - observer_gcrs
        alt, _, _ = difference.altaz()

        if alt.degrees > min_elevation:
            visible_satellites.append(sat)

    return visible_satellites


def filter_constellations(satellites, constellations_to_remove=['starlink', 'oneweb']):
    filtered = []
    for sat in satellites:
        name_lower = sat.name.lower()
        if any(constellation in name_lower for constellation in constellations_to_remove):
            continue
        filtered.append(sat)
    return filtered


def filter_geostationary(satellites):
    filtered = []
    for sat in satellites:
        n = sat.satellite.model.no_kozai
        n_rev_per_day = n * 1440.0 / (2 * np.pi)

        if n_rev_per_day > 6.0:
            filtered.append(sat)

    return filtered


def filter_heo(satellites, eccentricity_threshold=0.25):
    filtered = []
    for sat in satellites:
        e = sat.satellite.model.ecco
        if e < eccentricity_threshold:
            filtered.append(sat)
    return filtered


def filter_by_doppler(satellites, observer, t, center_freq, measured_freq, threshold=2000):
    passed = []

    t_sf = unix_to_skyfield(t)

    if observer.t_state != t_sf:
        obs_state = observer.location.at(t_sf)
        observer.set_state_at(t_sf, obs_state.position.km, obs_state.velocity.km_per_s)

    obs_p = observer.pos_gcrs
    obs_v = observer.vel_gcrs

    for sat in satellites:
        if sat.t_state != t_sf:
            sat_gcrs = sat.satellite.at(t_sf)
            sat.set_state_at(t_sf, sat_gcrs.position.km, sat_gcrs.velocity.km_per_s)

        p, v = sat.pos_gcrs, sat.vel_gcrs

        rel_pos = p - obs_p
        rel_vel = v - obs_v

        dist = np.linalg.norm(rel_pos)
        if dist == 0:
            continue

        range_rate = np.dot(rel_pos, rel_vel) / dist

        range_rate_m_s = range_rate * 1000.0
        predicted_shift = -(range_rate_m_s / C) * center_freq
        measured_shift = measured_freq - center_freq

        if abs(predicted_shift - measured_shift) < threshold:
            passed.append(sat)

    return passed
