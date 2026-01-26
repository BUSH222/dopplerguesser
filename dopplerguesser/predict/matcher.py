import numpy as np
from dopplerguesser.misc.constants import C, omega_earth


def score_candidates(candidates, measurements, center_freq, observer):
    results = []
    measurement_count = len(measurements)
    if measurement_count == 0:
        return []

    for sat in candidates:
        if sat.track_positions is None:
            continue

        squared_error_sum = 0.0
        valid_points = 0

        for dt, freq_meas in measurements:
            r_sat, v_sat = sat.get_state_from_track(dt)
            r_obs, _ = observer.get_state_from_track(dt)

            if r_sat is None or r_obs is None:
                continue

            v_obs = calculate_v_obs(r_obs)

            rr = calculate_range_rate_simple(r_sat, v_sat, r_obs, v_obs)

            shift = -(rr * 1000.0 / C) * center_freq
            measured_shift = freq_meas - center_freq
            resid = shift - measured_shift
            squared_error_sum += resid * resid
            valid_points += 1

        if valid_points > 0:
            rmse = np.sqrt(squared_error_sum / valid_points)
            results.append((rmse, sat))

    results.sort(key=lambda x: x[0])
    return results


def calculate_v_obs(r_obs):
    return np.array([-omega_earth * r_obs[1], omega_earth * r_obs[0], 0.0])


def calculate_range_rate_simple(r_sat, v_sat, r_obs, v_obs):
    rel_pos = r_sat - r_obs
    rel_vel = v_sat - v_obs
    dist = np.linalg.norm(rel_pos)
    if dist == 0:
        return 0.0
    return np.dot(rel_pos, rel_vel) / dist


def calculate_chi_squared(observed, expected):
    residuals = observed - expected
    return np.sum(residuals**2)
