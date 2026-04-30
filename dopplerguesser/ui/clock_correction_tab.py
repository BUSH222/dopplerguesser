import dearpygui.dearpygui as dpg
import numpy as np
import time
from dopplerguesser.script_control.runner import DPLLRunner
from dopplerguesser.misc.rigctl_query import query_rigctl
from dopplerguesser.config import config


class ClockCorrectionController:
    def __init__(self):
        self.runner = None
        self.plot_x = []
        self.plot_y = []
        self.last_update_time = 0
        self.limit = 1000

    def start(self):
        try:
            freq, sample_rate = query_rigctl()
            dpg.set_value("txt_center_freq_cc", f"Central Frequency (Hz): {freq}")
        except Exception as e:
            print(f"Rigctl query failed: {e}")
            freq, sample_rate = 0, 2000000
            dpg.set_value("txt_center_freq_cc", "Central Frequency (Hz): Error/Unknown")

        bw = int(dpg.get_value("combo_bw_cc"))
        use_fft = dpg.get_value("cb_use_fft_cc")

        params = {
            "s": sample_rate,
            "sample_format": "cs16",
            "center_freq": freq,
            "bw": bw,
            "use_fft_freq_find": use_fft
        }
        self.runner = DPLLRunner(port=12345, params=params)
        self.plot_x = []
        self.plot_y = []
        self.last_update_time = time.time()

        dpg.configure_item("drift_series", x=[], y=[])
        dpg.configure_item("btn_start_calib", label="Stop Calibration", callback=stop_calibration)
        dpg.configure_item("cb_use_fft_cc", enabled=False)
        self.runner.start(on_data_callback=self.handle_data)

    def stop(self):
        if self.runner:
            self.runner.stop()
            self.runner = None
        dpg.configure_item("btn_start_calib", label="Start Calibration", callback=start_calibration)
        dpg.configure_item("cb_use_fft_cc", enabled=True)

    def set_bw(self, sender, app_data, user_data):
        if self.runner and self.runner.is_running():
            self.runner.set_bandwidth(int(app_data))

    def handle_data(self, new_data_list):
        for sec_idx, val in new_data_list:
            self.plot_x.append(sec_idx)
            self.plot_y.append(val)
            dpg.set_value("clock_drift_text", f"Current clock drift: {val:.2f} Hz")

        now = time.time()
        if now - self.last_update_time > 0.2:
            self.update_plot()
            self.update_derivative_plot()
            self.update_metrics()
            self.last_update_time = now

    def update_metrics(self):
        if self.pll_locked():
            dpg.set_value("pll_status", "Locked")
            dpg.configure_item("pll_status", color=(100, 255, 100))
        else:
            dpg.set_value("pll_status", "Unlocked")
            dpg.configure_item("pll_status", color=(255, 0, 0))

        if len(self.plot_y) > 0:
            avg_30 = np.mean(self.plot_y[-30:])
            dpg.set_value("avg_drift_text", f"Average clock drift: {avg_30:.2f} Hz")

        slope = self.find_trend()
        dpg.set_value("slope_text", f"Current slope: {slope:.4f} Hz/s")

        threshold = 0.1
        if abs(slope) < threshold and self.pll_locked():
            dpg.set_value("clock_drift_status", "stable")
            dpg.configure_item("clock_drift_status", color=(100, 255, 100))
        else:
            dpg.set_value("clock_drift_status", "not stable")
            dpg.configure_item("clock_drift_status", color=(255, 0, 0))

    def update_plot(self):
        if not self.plot_x:
            return

        dpg.configure_item("drift_series",
                           x=self.plot_x[-self.limit:],
                           y=self.plot_y[-self.limit:])
        dpg.fit_axis_data("drift_x_axis")
        dpg.fit_axis_data("drift_y_axis")

    def update_derivative_plot(self):
        if len(self.plot_x) < 2:
            return

        dy = np.diff(self.plot_y)
        dx = np.diff(self.plot_x)
        derivative = dy / dx

        dpg.configure_item("raw_drift_derivative_series",
                           x=self.plot_x[1:][-self.limit:],
                           y=derivative[-self.limit:])
        dpg.fit_axis_data("raw_drift_derivative")

    def find_trend(self):
        if len(self.plot_x) < 2:
            return 0.0
        limit = 1000
        x = np.array(self.plot_x[-limit:])
        y = np.array(self.plot_y[-limit:])
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        return m

    def reset_calibration(self):
        self.plot_x = []
        self.plot_y = []
        dpg.configure_item("drift_series", x=[], y=[])
        dpg.configure_item("raw_drift_derivative_series", x=[], y=[])

        dpg.set_value("clock_drift_text", "Current clock drift: N/A Hz")
        dpg.set_value("avg_drift_text", "Average clock drift: N/A Hz")
        dpg.set_value("slope_text", "Current slope: N/A Hz/s")
        dpg.set_value("pll_status", "Unlocked")
        dpg.configure_item("pll_status", color=(255, 0, 0))
        dpg.set_value("clock_drift_status", "not stable")
        dpg.configure_item("clock_drift_status", color=(255, 0, 0))

    def pll_locked(self):
        if len(self.plot_y) < 20:
            return False
        recent_samples = self.plot_y[-20:]
        if max(recent_samples) - min(recent_samples) < 1000:
            return True
        return False


_controller = ClockCorrectionController()


def start_calibration(sender, app_data, user_data):
    _controller.start()


def stop_calibration(sender, app_data, user_data):
    _controller.stop()


def draw_clock_correction_tab():
    with dpg.tab(label="Clock Correction"):
        with dpg.collapsing_header(label="Clock Drift Calibration", default_open=True):
            dpg.add_text("Calibrate your SDR's clock drift here.")
            dpg.add_text("Aim at a known geostationary satellite or a stable signal source", wrap=350)
            dpg.add_text("Ensure rigctl server and IQ Exporter are running")

            dpg.add_button(label="Start Calibration", tag="btn_start_calib", width=-1,
                           callback=start_calibration)

            dpg.add_separator()
            dpg.add_text("Central Frequency (Hz): N/A", tag="txt_center_freq_cc")
            dpg.add_checkbox(label="use FFT-based frequency finding", tag="cb_use_fft_cc", default_value=True)
            with dpg.tooltip("cb_use_fft_cc"):
                dpg.add_text("works best when carriers are present")
            
            bw_list = [b.strip() for b in config["pll_bandwidths"].split(",")]
            default_bw = bw_list[2] if len(bw_list) > 2 else bw_list[0]
            dpg.add_text("PLL Bandwidth (Hz):")
            dpg.add_combo(bw_list, tag="combo_bw_cc", default_value=default_bw, callback=_controller.set_bw)
            
            dpg.add_spacer(height=5)
            dpg.add_text("Clock Readings:")

            dpg.add_text("Current clock drift: N/A Hz", tag="clock_drift_text", color=(255, 200, 100))
            dpg.add_text("Average clock drift: N/A Hz", tag="avg_drift_text", color=(200, 200, 255))
            dpg.add_text("Current slope: N/A Hz/s", tag="slope_text", color=(200, 200, 255))

            with dpg.group(horizontal=True):
                dpg.add_text("PLL:")
                dpg.add_text("Unlocked", tag="pll_status", color=(255, 0, 0))

            with dpg.group(horizontal=True):
                dpg.add_text("Clock is")
                dpg.add_text("not stable", tag="clock_drift_status", color=(255, 0, 0))
            with dpg.collapsing_header(label="Drift History", default_open=False):
                with dpg.plot(label="Drift History", height=300, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Sample", tag="drift_x_axis")
                    with dpg.plot_axis(dpg.mvYAxis, label="Drift (Hz)", tag="drift_y_axis"):
                        dpg.add_line_series([], [], label="Filtered Drift", tag="drift_series")
                    with dpg.plot_axis(dpg.mvYAxis, label="First Derivative of Drift (Hz)",
                                       tag="raw_drift_derivative"):
                        dpg.add_line_series([], [], label="Raw Drift Derivative", tag="raw_drift_derivative_series")
                dpg.add_button(label="Reset Calibration", width=-1,
                               callback=lambda s, a, u: _controller.reset_calibration())
