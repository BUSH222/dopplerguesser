import numpy as np
from skyfield.framelib import itrs
from dopplerguesser.misc.constants import mu, omega_earth


def propagate_fg_elliptic(sat_gcrs, t_sf, t_required, max_iter=10, tol=1e-12):
    if t_required.tt == t_sf.tt:
        return sat_gcrs.position.km, sat_gcrs.velocity.km_per_s

    r0 = sat_gcrs.position.km
    v0 = sat_gcrs.velocity.km_per_s

    r0_norm = np.linalg.norm(r0)
    v0_norm = np.linalg.norm(v0)

    dt = (t_required.tt - t_sf.tt) * 86400.0

    energy = 0.5 * v0_norm**2 - mu / r0_norm
    if energy >= 0:
        # non elliptic orbit, this will never happen
        return r0, v0

    a = -mu / (2.0 * energy)
    n = np.sqrt(mu / a**3)
    rv_dot = np.dot(r0, v0)
    sqrt_mu_a = np.sqrt(mu * a)

    DeltaE = n * dt

    for _ in range(max_iter):
        sinE = np.sin(DeltaE)
        cosE = np.cos(DeltaE)

        F = (DeltaE - (1.0 - r0_norm / a) * sinE
             + (rv_dot / sqrt_mu_a) * (1.0 - cosE) - n * dt)
        dF = (1.0 - (1.0 - r0_norm / a) * cosE
              + (rv_dot / sqrt_mu_a) * sinE)

        dE = -F / dF
        DeltaE += dE
        if abs(dE) < tol:
            break

    sinE = np.sin(DeltaE)
    cosE = np.cos(DeltaE)

    f = 1.0 - (a / r0_norm) * (1.0 - cosE)
    g = dt + (1.0 / n) * (sinE - DeltaE)

    r = f * r0 + g * v0
    r_norm = np.linalg.norm(r)

    fdot = -(sqrt_mu_a / (r_norm * r0_norm)) * sinE
    gdot = 1.0 - (a / r_norm) * (1.0 - cosE)

    v = fdot * r0 + gdot * v0

    return r, v


def init_earth_rotation(station, t_ref):
    r0_itrs = station.itrs_xyz.km
    R_gcrs2itrs = itrs.rotation_at(t_ref)
    R_itrs2gcrs = R_gcrs2itrs.T
    return r0_itrs, R_itrs2gcrs


def propagate_earth_rotation(r_itrs, R_itrs2gcrs_t0, dt_sec):
    r_gcrs_t0 = R_itrs2gcrs_t0 @ r_itrs
    angle = omega_earth * dt_sec
    c, s = np.cos(angle), np.sin(angle)

    x, y, z = r_gcrs_t0
    r_rotated = np.array([
        x*c - y*s,
        x*s + y*c,
        z
    ])

    return r_rotated


def calculate_range_rate(r_sat, v_sat, r_obs):
    v_obs = np.array([-omega_earth * r_obs[1], omega_earth * r_obs[0], 0.0])

    rel_pos = r_sat - r_obs
    rel_vel = v_sat - v_obs

    dist = np.linalg.norm(rel_pos)
    if dist == 0:
        return 0.0

    return np.dot(rel_pos, rel_vel) / dist
