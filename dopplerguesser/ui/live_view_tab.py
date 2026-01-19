import dearpygui.dearpygui as dpg


def draw_live_view_tab():
    with dpg.tab(label="Live View"):
        with dpg.collapsing_header(label="Signal Input", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text("Status:")
                dpg.add_text("Disconnected", color=(255, 100, 100), tag="status_text")

            dpg.add_button(label="Connect to GNURadio", width=-1,
                           callback=lambda: print("Connecting to ZMQ..."))

            dpg.add_separator()
            dpg.add_text("Signal Parameters")
            dpg.add_input_float(label="Center Freq (Hz)", default_value=2_252_500_000,
                                format="%.0f", step=1000)
            dpg.add_input_float(label="Clock Error (Hz)", default_value=0.0, step=10)

            dpg.add_spacer(height=5)
            dpg.add_text("Live Readings:")
            with dpg.group(horizontal=True):
                dpg.add_text("Doppler Offset: ")
                dpg.add_text("0.0 Hz", tag="live_doppler_text", color=(100, 255, 100))

            with dpg.group(horizontal=True):
                dpg.add_text("Rel. Velocity: ")
                dpg.add_text("0.0 m/s", tag="live_velocity_text", color=(100, 255, 255))

        with dpg.collapsing_header(label="Predict", default_open=True):
            dpg.add_button(label="Start predicting", width=-1,
                           callback=lambda: print("Starting prediction..."))
            dpg.add_text("Likelihood based on trajectory:")

            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                           borders_innerV=True, borders_outerV=True, row_background=True):
                dpg.add_table_column(label="Satellite", width_stretch=True)
                dpg.add_table_column(label="Conf.", width_fixed=True, init_width_or_weight=50)

                with dpg.table_row():
                    dpg.add_text("satellite 1")
                    dpg.add_text("83%")
                with dpg.table_row():
                    dpg.add_text("satellite 2")
                    dpg.add_text("10%")
                with dpg.table_row():
                    dpg.add_text("satellite 3")
                    dpg.add_text("5%")
                with dpg.table_row():
                    dpg.add_text("satellite 4")
                    dpg.add_text("1%")
                with dpg.table_row():
                    dpg.add_text("satellite 5")
                    dpg.add_text("0.5%")

        with dpg.collapsing_header(label="Doppler Curve", default_open=True):
            with dpg.plot(label="Doppler History", height=200, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                with dpg.plot_axis(dpg.mvYAxis, label="Shift (Hz)"):
                    dpg.add_line_series([0, 10, 20, 30], [0, 500, 1000, 1500], label="Measured")
                    dpg.add_line_series([0, 10, 20, 30], [0, 520, 1010, 1480], label="Predicted (Top)")
