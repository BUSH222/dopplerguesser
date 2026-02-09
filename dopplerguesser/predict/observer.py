from skyfield.api import wgs84
import numpy as np
from dopplerguesser.predict.propagator import init_earth_rotation, propagate_earth_rotation
from dopplerguesser.misc.constants import omega_earth
from dopplerguesser.misc.timetools import unix_to_skyfield


class Observer:
    def __init__(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt)

        self.t_state = None
        self.pos_gcrs = None
        self.vel_gcrs = None

        self.track_t_start = None
        self.track_positions = None
        self.track_velocities = None

    def update_location(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt)

    def set_state_at(self, t, pos, vel):
        self.t_state = t
        self.pos_gcrs = pos
        self.vel_gcrs = vel

    def set_track(self, t_start, positions, velocities):
        self.track_t_start = t_start
        self.track_positions = positions
        self.track_velocities = velocities

    def compute_track(self, t_start_unix, duration=1000, step=1):
        t_start_sf = unix_to_skyfield(t_start_unix)
        r0_itrs, R_itrs2gcrs_t0 = init_earth_rotation(self.location, t_start_sf)

        positions = []
        velocities = []
        times = np.arange(0, duration, step)

        for dt in times:
            r_gcrs = propagate_earth_rotation(r0_itrs, R_itrs2gcrs_t0, dt)
            v_gcrs = np.array([
                -omega_earth * r_gcrs[1],
                omega_earth * r_gcrs[0],
                0.0
            ])

            positions.append(r_gcrs)
            velocities.append(v_gcrs)

        self.set_track(t_start_sf, np.array(positions), np.array(velocities))

    def compute_track_precise(self, t_start_unix, duration=1000, step=1):
        '''Expensive function that computes the track by querying skyfield for each time step.'''
        t_start_sf = unix_to_skyfield(t_start_unix)
        positions, velocities = [], []
        times = np.arange(0, duration, step)
        for dt in times:
            t_req = t_start_sf + dt/86400.0
            obs_state = self.location.at(t_req)
            pos = obs_state.position.km
            vel = obs_state.velocity.km_per_s
            positions.append(pos)
            velocities.append(vel)
        self.set_track(t_start_sf, np.array(positions), np.array(velocities))

    def get_state_from_track(self, t_offset):
        if self.track_positions is None:
            return None, None

        idx = int(t_offset)
        if idx < 0:
            idx = 0
        if idx >= len(self.track_positions) - 1:
            idx = len(self.track_positions) - 2

        frac = t_offset - idx

        p0 = self.track_positions[idx]
        p1 = self.track_positions[idx+1]
        v0 = self.track_velocities[idx]
        v1 = self.track_velocities[idx+1]

        pos = p0 + (p1 - p0) * frac
        vel = v0 + (v1 - v0) * frac

        return pos, vel
