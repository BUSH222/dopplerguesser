from skyfield.api import wgs84


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
