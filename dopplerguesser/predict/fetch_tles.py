from dopplerguesser.predict.satellite import Satellite
import requests


def fetch_tles(ts):
    tlesource = requests.get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active").text.strip().split("\n")
    tles = [tlesource[i:i+3] for i in range(0, len(tlesource), 3)]
    satellites = []
    for tle in tles:
        name, line1, line2 = tle
        satellites.append(Satellite(name.strip(), line1, line2, ts))
    return satellites
