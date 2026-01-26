import numpy as np
from dopplerguesser.misc.constants import C
from dopplerguesser.predict.observer import Observer
from dopplerguesser.predict.satellite import Satellite


def filter_visibility(satellites: list[Satellite], observer: Observer, t_sf, min_elevation=0.0):
    visible_satellites = []

    observer_gcrs = observer.location.location.at(t_sf)

    for sat in satellites:
        difference = sat.satellite.at(t_sf) - observer_gcrs
        alt, _, _ = difference.altaz()

        if alt.degrees > min_elevation:
            visible_satellites.append(sat)

    return visible_satellites


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


def filter_by_doppler(satellites, observer, t_sf, center_freq, measured_freq, threshold=2000):
    passed = []

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
