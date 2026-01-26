from skyfield.api import EarthSatellite


class Satellite:
    def __init__(self, name, tle_line1, tle_line2, ts):
        self.name = name
        self.tle_line1 = tle_line1
        self.tle_line2 = tle_line2
        self.ts = ts
        self.satellite = EarthSatellite(tle_line1, tle_line2, name, ts)
