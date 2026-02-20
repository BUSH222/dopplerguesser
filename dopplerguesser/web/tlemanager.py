import requests
import os
import zipfile
from io import BytesIO


def update_tles(sources=['celestrak', 'space-track', 'classified'], space_track_credentials=None):
    celestraksource, spacetracksource, classifiedsource = None, None, None
    urlcelestrak = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active"
    urlst = 'https://www.space-track.org/basicspacedata/query/class/gp/format/3le/decay_date/null-val/epoch/%3Enow-14/'
    urlclassified = 'https://mmccants.org/tles/classfd.zip'
    try:
        if 'celestrak' in sources:
            celestraksource = requests.get(urlcelestrak).text.strip().split("\n")
        if 'space-track' in sources and space_track_credentials is not None:
            with requests.session() as session:
                login_url = "https://www.space-track.org/ajaxauth/login"
                payload = {
                    'identity': space_track_credentials['username'],
                    'password': space_track_credentials['password']
                }
                session.post(login_url, data=payload)
                spacetracksource = session.get(urlst).text.strip().split("\n")
        if 'classified' in sources:
            resp = requests.get(urlclassified, stream=True)
            resp.raise_for_status()
            zip_buffer = BytesIO(resp.content)
            with zipfile.ZipFile(zip_buffer) as z:
                with z.open('classfd.tle') as f:
                    tle_data = f.read().decode("utf-8")
                    classifiedsource = tle_data.strip().split("\n")
        tles = {}
        for source in [celestraksource, spacetracksource, classifiedsource]:
            if source is not None:
                for i in range(0, len(source), 3):
                    tle = source[i:i+3]
                    if len(tle) == 3:
                        norad_cat_id = tle[1][2:7]
                        if norad_cat_id not in tles:
                            tles[norad_cat_id] = tle
                        else:
                            epoch = tle[2][18:32]
                            existing_epoch = tles[norad_cat_id][2][18:32]
                            if epoch > existing_epoch:
                                tles[norad_cat_id] = tle
        tle_file_path = os.path.join(os.path.dirname(__file__), "tles.txt")
        with open(tle_file_path, "w") as f:
            for tle in tles.values():
                f.write("\n".join(tle) + "\n")
        return 'ok'
    except Exception as e:
        print(f"Error updating TLEs: {e}")
        return e


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
