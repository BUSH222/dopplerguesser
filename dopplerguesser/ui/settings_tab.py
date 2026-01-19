import dearpygui.dearpygui as dpg
from dopplerguesser.config import config


def save_settings(sender, app_data, user_data):
    config.set("lat", round(dpg.get_value("settings_lat"), 5))
    config.set("lon", round(dpg.get_value("settings_lon"), 5))
    config.set("alt", round(dpg.get_value("settings_alt"), 2))
    config.set("alive_only", dpg.get_value("settings_alive_only"))
    config.set("gr_path", dpg.get_value("settings_gr_path"))
    config.set("gr_tcp", dpg.get_value("settings_gr_tcp"))
    config.set("debug_tab", dpg.get_value("settings_debug_tab"))

    config.save()


def draw_settings_tab():
    config.load()
    with dpg.tab(label="Settings"):

        with dpg.collapsing_header(label="Observer Location", default_open=True):
            dpg.add_input_float(label="Lat (deg)", tag="settings_lat", default_value=config.get("lat"))
            dpg.add_input_float(label="Lon (deg)", tag="settings_lon", default_value=config.get("lon"))
            dpg.add_input_float(label="Alt (m)", tag="settings_alt", default_value=config.get("alt"))

        with dpg.collapsing_header(label="Databases"):
            dpg.add_button(label="Update TLEs (Celestrak)", width=-1,
                           callback=lambda: print("Fetching TLEs..."))
            dpg.add_button(label="Fetch SatNOGS Transmitters", width=-1,
                           callback=lambda: print("Fetching SatNOGS DB..."))

            dpg.add_separator()
            dpg.add_text("SatNOGS Search Filters")
            dpg.add_checkbox(label="Alive Satellites Only", tag="settings_alive_only",
                             default_value=config.get("alive_only"))

        with dpg.collapsing_header(label="Connections"):
            dpg.add_text("GNURadio Python Path")
            dpg.add_input_text(tag="settings_gr_path", default_value=config.get("gr_path"), width=-1)
            dpg.add_text("GNURadio TCP Server URL")
            dpg.add_input_text(tag="settings_gr_tcp", default_value=config.get("gr_tcp"), width=-1)

        with dpg.collapsing_header(label="Misc"):
            dpg.add_checkbox(label="Enable Debug Tab", tag="settings_debug_tab", default_value=config.get("debug_tab"))

        dpg.add_button(label="Save Settings", width=-1, callback=save_settings, tag="save_settings_button")
        # with dpg.tooltip("save_settings_button"):
        #     dpg.add_text("Restart required for some changes to take effect.")
