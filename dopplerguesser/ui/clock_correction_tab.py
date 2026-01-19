import dearpygui.dearpygui as dpg


def draw_clock_correction_tab():
    with dpg.tab(label="Clock Correction"):
        with dpg.collapsing_header(label="Clock Drift Calibration", default_open=True):
            dpg.add_text("Calibrate your SDR's clock drift here.")
            dpg.add_text("Aim at a known geostationary satellite", wrap=400)
            dpg.add_listbox(label="Select Satellite", items=["USA-230", "ELEKTRO-L N3", "Other"],
                            width=-1)
            dpg.add_input_float(label="Frequency (MHz)", default_value=2262.5, format="%.2f MHz")
            dpg.add_button(label="Start Calibration", width=-1,
                           callback=lambda: print("Starting clock drift calibration..."))
            dpg.add_text("Current Drift: 0.0 Hz", tag="clock_drift_text", color=(255, 200, 100))
