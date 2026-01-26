from skyfield.api import wgs84


class Observer:
    def __init__(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt)

    def update_location(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.location = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt)
