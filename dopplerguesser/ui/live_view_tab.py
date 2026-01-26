import dearpygui.dearpygui as dpg
import os
from dopplerguesser.script_control.runner import FlowgraphRunner
from dopplerguesser.misc.rigctl_query import query_rigctl

C = 299792458


class LiveViewController:
    def __init__(self):
        self.runner = None
        self.plot_x = []
        self.plot_y = []
        self.center_freq = 0
        self.clock_error = 0
        self.running = False
        self.limit = 1000

    def start_monitoring(self):
        if self.running:
            return

        self.clock_error = dpg.get_value("input_clock_error")

        sample_rate = 2e6
        correct_iq = dpg.get_value("chk_live_dc_spike")

        try:
            freq, sr = query_rigctl()
            self.center_freq = freq
            sample_rate = sr
            dpg.set_value("txt_center_freq", f"Central Frequency (Hz): {freq}")
        except Exception as e:
            print(f"Rigctl query failed: {e}")
            dpg.set_value("txt_center_freq", "Central Frequency (Hz): Error/Unknown")

        params = {
            "sample_rate": sample_rate,
            "remove_dc_spike": int(correct_iq)
        }

        script_path = os.path.abspath(os.path.join("gr_scripts", "pll_estimator.py"))
        self.runner = FlowgraphRunner(script_path, port=12346, params=params)
        self.plot_x = []
        self.plot_y = []
        dpg.configure_item("live_doppler_series", x=[], y=[])

        self.runner.start(on_data_callback=self.handle_data)
        self.running = True

        dpg.configure_item("btn_live_connect", label="Disconnect", callback=stop_live_view)

    def stop_monitoring(self):
        if self.runner:
            self.runner.stop()
            self.runner = None
        self.running = False
        dpg.configure_item("btn_live_connect", label="Connect", callback=start_live_view)

    def handle_data(self, data_list):
        for sec, val in data_list:
            self.plot_x.append(sec)
            self.plot_y.append(val)
            self.update_ui(val)

        self.update_plot()

    def update_ui(self, current_offset):
        if self.pll_locked():
            dpg.set_value("live_pll_status", "PLL is Locked")
            dpg.configure_item("live_pll_status", color=(100, 255, 100))
        else:
            dpg.set_value("live_pll_status", "PLL is Unlocked")
            dpg.configure_item("live_pll_status", color=(255, 100, 100))
        dpg.set_value("live_doppler_text", f"{current_offset:.2f} Hz")

        if self.center_freq > 0:
            # v = ((offset - clock_error) / f0) * c
            shift = current_offset - self.clock_error
            v = (shift / self.center_freq) * C
            dpg.set_value("live_velocity_text", f"{v:.2f} m/s")

    def update_plot(self):
        if not self.plot_x:
            return

        x_data = self.plot_x[-self.limit:]
        y_data = self.plot_y[-self.limit:]

        dpg.configure_item("live_doppler_series", x=x_data, y=y_data)
        dpg.fit_axis_data("live_doppler_xaxis")
        dpg.fit_axis_data("live_doppler_yaxis")

    def pll_locked(self):
        if len(self.plot_y) < 20:
            return False
        recent = self.plot_y[-20:]
        if max(recent) - min(recent) < 1000:
            return True
        return False


_live_controller = LiveViewController()


def start_live_view(sender, app_data, user_data):
    _live_controller.start_monitoring()


def stop_live_view(sender, app_data, user_data):
    _live_controller.stop_monitoring()


def draw_live_view_tab():
    with dpg.tab(label="Live View"):
        with dpg.collapsing_header(label="Signal Input", default_open=True):
            dpg.add_text("Connect to your SDR and start receiving live data.")
            dpg.add_text("Ensure rigctl server and IQ Exporter are running")
            dpg.add_button(label="Connect", tag="btn_live_connect", width=-1, callback=start_live_view)

            dpg.add_separator()
            dpg.add_text("Parameters")
            dpg.add_text("Central Frequency (Hz): N/A", tag="txt_center_freq")
            dpg.add_input_float(label="Clock Error (Hz)", tag="input_clock_error", default_value=0.0, step=10)
            dpg.add_checkbox(label="Remove DC Spike", tag="chk_live_dc_spike", default_value=True)

            dpg.add_spacer(height=5)
            dpg.add_text("Live Readings:")

            dpg.add_text('PLL is unlocked', color=(255, 100, 100), tag="live_pll_status")
            with dpg.group(horizontal=True):
                dpg.add_text("Doppler Offset: ")
                dpg.add_text("0.0 Hz", tag="live_doppler_text", color=(100, 255, 100))

            with dpg.group(horizontal=True):
                dpg.add_text("Rel. Velocity: ")
                dpg.add_text("0.0 m/s", tag="live_velocity_text", color=(100, 255, 255))

        with dpg.collapsing_header(label="Predict", default_open=True):
            dpg.add_text('Confirm PLL is locked and doppler readings are stable before predicting.')
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
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="live_doppler_xaxis")
                with dpg.plot_axis(dpg.mvYAxis, label="Shift (Hz)", tag="live_doppler_yaxis"):
                    dpg.add_line_series([], [], label="Measured", tag="live_doppler_series")
                dpg.add_button(label="Clear", width=-1, callback=lambda: _live_controller.clear_plot())
