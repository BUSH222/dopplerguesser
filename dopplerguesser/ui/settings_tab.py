import threading
import dearpygui.dearpygui as dpg
from dopplerguesser.config import config
from dopplerguesser.web.tlemanager import update_tles


def save_settings(sender, app_data, user_data):
    config["lat"] = round(dpg.get_value("settings_lat"), 5)
    config["lon"] = round(dpg.get_value("settings_lon"), 5)
    config["alt"] = round(dpg.get_value("settings_alt"), 2)
    config["tle_source_celestrak"] = dpg.get_value("settings_tle_source_celestrak")
    config["tle_source_spacetrack"] = dpg.get_value("settings_tle_source_spacetrack")
    config["tle_source_classified"] = dpg.get_value("settings_tle_source_classified")
    config["tle_source_from_file"] = dpg.get_value("settings_tle_source_from_file")
    config["tle_file_path"] = dpg.get_value("settings_tle_file_path")
    config["spacetrack_login"] = dpg.get_value("settings_spacetrack_login")
    config["spacetrack_password"] = dpg.get_value("settings_spacetrack_password")
    config["gr_path"] = dpg.get_value("settings_gr_path")
    config["gr_tcp"] = dpg.get_value("settings_gr_tcp")

    config["filter_constellations"] = dpg.get_value("settings_filter_constellations")
    config["filter_constellations_list"] = dpg.get_value("settings_filter_constellations_list")
    config["filter_heo"] = dpg.get_value("settings_filter_heo")
    config["filter_debris"] = dpg.get_value("settings_filter_debris")
    config["filter_by_epoch"] = dpg.get_value("settings_filter_by_epoch")
    config["max_tle_age_days"] = int(dpg.get_value("settings_max_tle_age_days"))
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

        sources = []
        if dpg.get_value("settings_tle_source_celestrak"):
            sources.append('celestrak')
        if dpg.get_value("settings_tle_source_spacetrack"):
            sources.append('space-track')
        if dpg.get_value("settings_tle_source_classified"):
            sources.append('classified')
        if dpg.get_value("settings_tle_source_from_file"):
            sources.append('from_file')

        space_track_credentials = None
        login = dpg.get_value("settings_spacetrack_login")
        password = dpg.get_value("settings_spacetrack_password")
        if login and password:
            space_track_credentials = {
                'username': login,
                'password': password
            }

        file_path = dpg.get_value("settings_tle_file_path")
        file_path = file_path if file_path else None

        update_tles(sources=sources, space_track_credentials=space_track_credentials, file_path=file_path)
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
            dpg.add_input_float(label="Lat (deg)", tag="settings_lat", default_value=config["lat"], format="%.5f")
            dpg.add_input_float(label="Lon (deg)", tag="settings_lon", default_value=config["lon"], format="%.5f")
            dpg.add_input_float(label="Alt (m)", tag="settings_alt", default_value=config["alt"], format="%.2f")

        with dpg.collapsing_header(label="Databases"):
            dpg.add_button(label="Update TLEs", width=-1,
                           callback=update_tles_callback, tag="update_tles_button")
            dpg.add_loading_indicator(tag="tles_loading_indicator", show=False, speed=10)
            dpg.add_text("", tag="tles_status_text", show=False)

            dpg.add_text("TLE Sources:")
            dpg.add_checkbox(label="Celestrak", tag="settings_tle_source_celestrak",
                             default_value=config.get("tle_source_celestrak", True))
            dpg.add_checkbox(label="Space-track", tag="settings_tle_source_spacetrack",
                             default_value=config.get("tle_source_spacetrack", False))
            dpg.add_checkbox(label="Mike McCants' Classified", tag="settings_tle_source_classified",
                             default_value=config.get("tle_source_classified", False))
            dpg.add_checkbox(label="From file", tag="settings_tle_source_from_file",
                             default_value=config.get("tle_source_from_file", False))

            dpg.add_text("TLE file path:")
            dpg.add_input_text(tag="settings_tle_file_path",
                               default_value=config.get("tle_file_path", ""), width=-1)
            dpg.add_text("Space-track login:")
            dpg.add_input_text(tag="settings_spacetrack_login",
                               default_value=config.get("spacetrack_login", ""), width=-1)
            dpg.add_text("Space-track password:")
            dpg.add_input_text(tag="settings_spacetrack_password",
                               default_value=config.get("spacetrack_password", ""), width=-1, password=True)

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
            dpg.add_checkbox(label="Filter debris", tag="settings_filter_debris",
                             default_value=config.get("filter_debris", True))
            dpg.add_checkbox(label="Filter by epoch", tag="settings_filter_by_epoch",
                             default_value=config.get("filter_by_epoch", True))
            dpg.add_text("Max TLE age (days):")
            dpg.add_input_int(tag="settings_max_tle_age_days",
                              default_value=config.get("max_tle_age_days", 30), width=-1)
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
