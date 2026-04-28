import json
import os


class ConfigManager:
    _instance = None
    CONFIG_FILE = "config.json"
    DEFAULTS = {
        "lat": 0.0,
        "lon": 0.0,
        "alt": 0.0,
        "alive_only": True,
        "debug_tab": False,
        "filter_constellations": True,
        "filter_constellations_list": "starlink,oneweb",
        "filter_heo": True,
        "filter_doppler": False,
        "filter_doppler_threshold": 10000,
        "filter_visibility_min_elevation": 0,
        "propagation_cache_duration": 1000,
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._settings = cls.DEFAULTS.copy()
            cls._instance.load()
        return cls._instance

    def load(self):
        print("Reloading settings from config.json")
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(self._settings, f, indent=4)
            print("Settings saved to config.json")
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value

    def __getitem__(self, item):
        return self._settings[item]

    def __setitem__(self, key, value):
        self._settings[key] = value


config = ConfigManager()
