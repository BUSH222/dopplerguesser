import dearpygui.dearpygui as dpg
import json
import os
from dopplerguesser.config import CONFIG_FILE


def load_settings():
    defaults = {
        "lat": 55.7,
        "lon": 37.1,
        "alt": 170.0,
        "alive_only": True,
        "gr_path": "",
        "gr_tcp": "localhost:12346",
        "debug_tab": False,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        except Exception as e:
            print(f"Error loading config: {e}")
    return defaults


def save_settings(sender, app_data, user_data):
    settings = {
        "lat": dpg.get_value("settings_lat"),
        "lon": dpg.get_value("settings_lon"),
        "alt": dpg.get_value("settings_alt"),
        "alive_only": dpg.get_value("settings_alive_only"),
        "gr_path": dpg.get_value("settings_gr_path"),
        "gr_tcp": dpg.get_value("settings_gr_tcp"),
        "debug_tab": dpg.get_value("settings_debug_tab"),
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        print("Settings saved to config.json")
    except Exception as e:
        print(f"Error saving config: {e}")


def draw_settings_tab():
    defaults = load_settings()
    with dpg.tab(label="Settings"):

        with dpg.collapsing_header(label="Observer Location", default_open=True):
            dpg.add_input_float(label="Lat (deg)", tag="settings_lat", default_value=defaults["lat"])
            dpg.add_input_float(label="Lon (deg)", tag="settings_lon", default_value=defaults["lon"])
            dpg.add_input_float(label="Alt (m)", tag="settings_alt", default_value=defaults["alt"])

        with dpg.collapsing_header(label="Databases"):
            dpg.add_button(label="Update TLEs (Celestrak)", width=-1,
                           callback=lambda: print("Fetching TLEs..."))
            dpg.add_button(label="Fetch SatNOGS Transmitters", width=-1,
                           callback=lambda: print("Fetching SatNOGS DB..."))

            dpg.add_separator()
            dpg.add_text("SatNOGS Search Filters")
            dpg.add_checkbox(label="Alive Satellites Only", tag="settings_alive_only",
                             default_value=defaults["alive_only"])

        with dpg.collapsing_header(label="Connections"):
            dpg.add_input_text(label="GNURadio Python Path", tag="settings_gr_path",
                               default_value=defaults["gr_path"], width=-1)
            dpg.add_input_text(label="GNURadio TCP server URL", tag="settings_gr_tcp",
                               default_value=defaults["gr_tcp"], width=-1)

        with dpg.collapsing_header(label="Misc"):
            dpg.add_checkbox(label="Enable Debug Tab", tag="settings_debug_tab", default_value=defaults["debug_tab"])

        dpg.add_button(label="Save Settings", width=-1, callback=save_settings)
