import numpy as np
from skyfield.framelib import itrs
from dopplerguesser.misc.timetools import unix_to_skyfield
from dopplerguesser.misc.constants import C


def generate_doppler_curve(satellite, observer, center_freq, t_start_unix, duration=500, step=1, simulated_noise=100):
    '''Debugging utility, do not use in main code, expensive.'''
    t_start_sf = unix_to_skyfield(t_start_unix)
    times = np.arange(0, duration, step)
    doppler_shifts = []
    for dt in times:
        observer_grcs = observer.location.at(t_start_sf + dt/86400.0)
        satellite_grcs = satellite.satellite.at(t_start_sf + dt/86400.0)
        pos = observer_grcs - satellite_grcs
        _, _, _, _, _, range_rate = pos.frame_latlon_and_rates(itrs)
        frequency = center_freq * (1 - (range_rate.m_per_s) / C)
        noise = np.random.uniform(-simulated_noise, simulated_noise)
        doppler_shifts.append(frequency + noise)
    return list(zip(times, doppler_shifts))
