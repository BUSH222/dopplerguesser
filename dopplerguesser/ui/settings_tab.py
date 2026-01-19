import dearpygui.dearpygui as dpg


def draw_settings_tab():
    with dpg.tab(label="Settings"):

        with dpg.collapsing_header(label="Observer Location", default_open=True):
            dpg.add_input_float(label="Lat (deg)", default_value=55.7)
            dpg.add_input_float(label="Lon (deg)", default_value=37.1)
            dpg.add_input_float(label="Alt (m)", default_value=170.0)

        with dpg.collapsing_header(label="Databases"):
            dpg.add_button(label="Update TLEs (Celestrak)", width=-1,
                           callback=lambda: print("Fetching TLEs..."))
            dpg.add_button(label="Fetch SatNOGS Transmitters", width=-1,
                           callback=lambda: print("Fetching SatNOGS DB..."))

            dpg.add_separator()
            dpg.add_text("SatNOGS Search Filters")
            dpg.add_checkbox(label="Alive Satellites Only", default_value=True)

        with dpg.collapsing_header(label="Connections"):
            dpg.add_input_text(label="GNURadio Python Path", default_value="", width=-1)
            dpg.add_input_text(label="GNURadio TCP server URL", default_value="localhost:12346", width=-1)

        with dpg.collapsing_header(label="Misc"):
            dpg.add_checkbox(label="Enable Debug Tab", default_value=False)
