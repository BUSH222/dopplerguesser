from dopplerguesser.predict.satellite import Satellite
from dopplerguesser.web.tlemanager import load_tles


def fetch_tles(ts, tle_file_path=None):
    tles = load_tles(tle_file_path=tle_file_path)
    satellites = []
    for tle in tles:
        name, line1, line2 = tle
        satellites.append(Satellite(name.strip(), line1, line2, ts))
    return satellites
