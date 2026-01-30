import threading
import dearpygui.dearpygui as dpg
from dopplerguesser.config import config
from dopplerguesser.web.tlemanager import update_tles


def save_settings(sender, app_data, user_data):
    config["lat"] = round(dpg.get_value("settings_lat"), 5)
    config["lon"] = round(dpg.get_value("settings_lon"), 5)
    config["alt"] = round(dpg.get_value("settings_alt"), 2)
    config["alive_only"] = dpg.get_value("settings_alive_only")
    config["gr_path"] = dpg.get_value("settings_gr_path")
    config["gr_tcp"] = dpg.get_value("settings_gr_tcp")

    config["filter_constellations"] = dpg.get_value("settings_filter_constellations")
    config["filter_constellations_list"] = dpg.get_value("settings_filter_constellations_list")
    config["filter_heo"] = dpg.get_value("settings_filter_heo")
    config["filter_doppler"] = dpg.get_value("settings_filter_doppler")
    config["filter_doppler_threshold"] = int(dpg.get_value("settings_filter_doppler_threshold"))
    config["filter_visibility_min_elevation"] = int(dpg.get_value("settings_filter_visibility_min_elevation"))

    config["propagation_cache_duration"] = int(dpg.get_value("settings_propagation_cache_duration"))

    config["debug_tab"] = dpg.get_value("settings_debug_tab")

    config.save()


def _update_tles_worker():
    try:
        dpg.configure_item("update_tles_button", enabled=False)
        dpg.configure_item("tles_status_text", default_value="Updating TLEs...")
        dpg.configure_item("tles_loading_indicator", show=True)

        update_tles()
    except Exception as e:
        dpg.configure_item("tles_status_text", show=True)
        dpg.configure_item("tles_status_text", default_value=f"Error updating TLEs: {e}")
    finally:
        dpg.configure_item("tles_loading_indicator", show=False)
        dpg.configure_item("update_tles_button", enabled=True)


def update_tles_callback(sender, app_data, user_data):
    threading.Thread(target=_update_tles_worker, daemon=True).start()


def draw_settings_tab():
    config.load()
    with dpg.tab(label="Settings"):

        with dpg.collapsing_header(label="Observer Location", default_open=True):
            dpg.add_input_float(label="Lat (deg)", tag="settings_lat", default_value=config["lat"])
            dpg.add_input_float(label="Lon (deg)", tag="settings_lon", default_value=config["lon"])
            dpg.add_input_float(label="Alt (m)", tag="settings_alt", default_value=config["alt"])

        with dpg.collapsing_header(label="Databases"):
            dpg.add_button(label="Update TLEs (Celestrak)", width=-1,
                           callback=update_tles_callback, tag="update_tles_button")
            dpg.add_loading_indicator(tag="tles_loading_indicator", show=False, speed=10)
            dpg.add_text("", tag="tles_status_text", show=False)
            dpg.add_button(label="Fetch SatNOGS Transmitters", width=-1, enabled=False)

            dpg.add_separator()
            dpg.add_text("SatNOGS Search Filters")
            dpg.add_checkbox(label="Alive Satellites Only", tag="settings_alive_only",
                             default_value=config["alive_only"])

        with dpg.collapsing_header(label="Connections"):
            dpg.add_text("GNURadio Python Path")
            dpg.add_input_text(tag="settings_gr_path", default_value=config["gr_path"], width=-1)
            dpg.add_text("GNURadio TCP Server URL")
            dpg.add_input_text(tag="settings_gr_tcp", default_value=config["gr_tcp"], width=-1)

        with dpg.collapsing_header(label="Filters"):
            dpg.add_checkbox(label="Filter satellite constellations", tag="settings_filter_constellations",
                             default_value=config["filter_constellations"])
            dpg.add_text("Comma-separated list of constellation names.")
            dpg.add_input_text(tag="settings_filter_constellations_list",
                               default_value=config["filter_constellations_list"], width=-1)
            dpg.add_checkbox(label="Filter HEO satellites", tag="settings_filter_heo",
                             default_value=config["filter_heo"])
            dpg.add_checkbox(label="Filter by initial doppler shift", tag="settings_filter_doppler",
                             default_value=config["filter_doppler"])
            dpg.add_text("Doppler Shift Threshold (Hz):")
            dpg.add_input_int(tag="settings_filter_doppler_threshold",
                              default_value=config["filter_doppler_threshold"])
            dpg.add_text("Visibility filter minimum elevation (deg):")
            dpg.add_input_int(tag="settings_filter_visibility_min_elevation",
                              default_value=config["filter_visibility_min_elevation"])

        with dpg.collapsing_header(label="Prediction"):
            dpg.add_text("Propagation cache duration (s):")
            dpg.add_input_int(tag="settings_propagation_cache_duration",
                              default_value=config["propagation_cache_duration"])
            dpg.add_text("PLL thresholds:")
            dpg.add_text('soon')

        with dpg.collapsing_header(label="Misc"):
            dpg.add_checkbox(label="Enable Debug Tab", tag="settings_debug_tab", default_value=config["debug_tab"])

        dpg.add_button(label="Save Settings", width=-1, callback=save_settings, tag="save_settings_button")
        # with dpg.tooltip("save_settings_button"):
        #     dpg.add_text("Restart required for some changes to take effect.")
