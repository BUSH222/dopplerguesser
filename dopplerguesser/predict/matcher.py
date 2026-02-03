import numpy as np
from dopplerguesser.misc.constants import C, omega_earth


def score_candidates(candidates, measurements, center_freq, observer):
    results = []
    measurement_count = len(measurements)
    if measurement_count == 0:
        return []

    obs_freqs = np.array([m[1] for m in measurements])
    obs_mean = np.mean(obs_freqs)
    obs_normalized = obs_freqs - obs_mean

    for sat in candidates:
        if sat.track_positions is None:
            continue

        pred_freqs = []
        valid_mask = []

        for dt, _ in measurements:
            r_sat, v_sat = sat.get_state_from_track(dt)
            r_obs, _ = observer.get_state_from_track(dt)

            if r_sat is None or r_obs is None:
                valid_mask.append(False)
                pred_freqs.append(0.0)
                continue

            valid_mask.append(True)
            v_obs = calculate_v_obs(r_obs)
            rr = calculate_range_rate_simple(r_sat, v_sat, r_obs, v_obs)
            shift = -(rr * 1000.0 / C) * center_freq
            pred_freqs.append(center_freq + shift)

        pred_freqs = np.array(pred_freqs)
        valid_mask = np.array(valid_mask)

        if not np.any(valid_mask):
            continue

        # Normalize predicted frequencies
        pred_mean = np.mean(pred_freqs[valid_mask])
        pred_normalized = pred_freqs - pred_mean

        # Calculate RMSE on normalized data
        residuals = (obs_normalized - pred_normalized)[valid_mask]
        rmse = np.sqrt(np.mean(residuals ** 2))

        results.append((sat, rmse))

    results.sort(key=lambda x: x[1])
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
