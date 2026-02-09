from skyfield.api import EarthSatellite, load
import numpy as np
from dopplerguesser.predict.propagator import propagate_fg_elliptic
from dopplerguesser.misc.timetools import unix_to_skyfield
from dopplerguesser.misc.mocks import SimpleTime, StateMock
timescale = load.timescale()


class Satellite:
    def __init__(self, name, tle_line1, tle_line2, ts):
        self.name = name
        self.tle_line1 = tle_line1
        self.tle_line2 = tle_line2
        self.ts = ts  # Unix timestamp
        self.satellite = EarthSatellite(tle_line1, tle_line2, name, timescale)

        # Initial skyfield state
        self.t_state = None
        self.pos_gcrs = None  # km
        self.vel_gcrs = None  # km/s

        # Track
        self.track_t_start = None
        self.track_positions = None
        self.track_velocities = None

    def set_state_at(self, t, pos, vel):
        self.t_state = t
        self.pos_gcrs = pos
        self.vel_gcrs = vel

    def set_track(self, t_start, positions, velocities):
        self.track_t_start = t_start
        self.track_positions = positions
        self.track_velocities = velocities

    def compute_initial_state(self, t_unix):
        t_sf = unix_to_skyfield(t_unix)
        sat_state = self.satellite.at(t_sf)
        pos = sat_state.position.km
        vel = sat_state.velocity.km_per_s
        self.set_state_at(t_sf, pos, vel)

    def compute_track(self, t_start_unix, duration=1000, step=1):
        t_start_sf = unix_to_skyfield(t_start_unix)

        if self.t_state == t_start_sf:
            initial_state = StateMock()
            initial_state.position = StateMock()
            initial_state.velocity = StateMock()
            initial_state.position.km = self.pos_gcrs
            initial_state.velocity.km_per_s = self.vel_gcrs
        else:
            print("WARNING: Computing initial position during track computation. This shouldn't happen.")
            initial_state = self.satellite.at(t_start_sf)

        positions = []
        velocities = []
        times = np.arange(0, duration, step)

        for dt in times:
            t_req = SimpleTime(t_start_sf.tt + dt/86400.0)
            r, v = propagate_fg_elliptic(initial_state, t_start_sf, t_req)
            positions.append(r)
            velocities.append(v)

        self.set_track(t_start_sf, np.array(positions), np.array(velocities))

    def compute_track_precise(self, t_start_unix, duration=1000, step=1):
        '''Expensive function that computes the track by querying skyfield for each time step.'''
        t_start_sf = unix_to_skyfield(t_start_unix)
        positions, velocities = [], []
        times = np.arange(0, duration, step)
        for dt in times:
            t_req = t_start_sf + dt/86400.0
            sat_state = self.satellite.at(t_req)
            pos = sat_state.position.km
            vel = sat_state.velocity.km_per_s
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
