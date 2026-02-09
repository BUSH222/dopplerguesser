import requests
import os


def update_tles():
    tlesource = requests.get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active").text.strip().split("\n")
    tle_file_path = os.path.join(os.path.dirname(__file__), "tles.txt")
    with open(tle_file_path, "w") as f:
        f.write("\n".join(tlesource) + "\n")


def load_tles(tle_file_path=None):
    if tle_file_path is None:
        tle_file_path = os.path.join(os.path.dirname(__file__), "tles.txt")
    else:
        tle_file_path = os.path.abspath(tle_file_path)

    tles = []
    if os.path.exists(tle_file_path):
        with open(tle_file_path, "r") as f:
            lines = f.readlines()
            tles = [lines[i:i+3] for i in range(0, len(lines), 3)]
    return tles
