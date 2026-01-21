import dearpygui.dearpygui as dpg
import numpy as np
import os
import time
from dopplerguesser.script_control.runner import FlowgraphRunner


class ClockCorrectionController:
    def __init__(self):
        self.runner = None
        self.data_buffer = np.array([], dtype=np.float32)
        self.window_size = 100
        self.processed_count = 0
        self.plot_x = []
        self.plot_y = []
        self.last_update_time = 0
        self.limit = 1000

    def start(self):
        script_path = os.path.abspath(os.path.join("gr_scripts", "pll_lock.py"))
        self.runner = FlowgraphRunner(script_path, port=12346)
        self.data_buffer = np.array([], dtype=np.float32)
        self.processed_count = 0
        self.plot_x = []
        self.plot_y = []
        self.last_update_time = time.time()

        dpg.configure_item("drift_series", x=[], y=[])
        dpg.configure_item("btn_start_calib", label="Stop Calibration", callback=stop_calibration)
        self.runner.start(on_data_callback=self.handle_data)

    def stop(self):
        if self.runner:
            self.runner.stop()
            self.runner = None
        dpg.configure_item("btn_start_calib", label="Start Calibration", callback=start_calibration)

    def handle_data(self, new_data):
        self.data_buffer = np.concatenate((self.data_buffer, new_data))

        if len(new_data) > 0:
            val = new_data[-1]
            dpg.set_value("clock_drift_text", f"Delta = {val:.2f} Hz")

        now = time.time()
        if now - self.last_update_time > 0.2:
            self.update_plot()
            self.update_derivative_plot()
            stable = self.update_stability_status()
            if stable:
                self.update_average_drift_display()
            else:
                dpg.set_value("average_clock_drift_text", "Average clock drift: N/A Hz")
            self.last_update_time = now

    def update_plot(self):
        if len(self.data_buffer) >= self.processed_count + self.window_size:
            chunk = self.data_buffer[self.processed_count:]
            window = np.ones(self.window_size) / self.window_size
            filtered = np.convolve(chunk, window, mode='valid')

            if len(filtered) > 0:
                current_len = len(self.plot_y)
                new_len = len(filtered)
                new_x = np.arange(current_len, current_len + new_len)

                self.plot_x.extend(new_x.tolist())
                self.plot_y.extend(filtered.tolist())
                self.processed_count += new_len

                dpg.configure_item("drift_series",
                                   x=self.plot_x[-self.limit:],
                                   y=self.plot_y[-self.limit:])
                dpg.fit_axis_data("drift_x_axis")
                dpg.fit_axis_data("drift_y_axis")

    def find_trend(self):
        if len(self.plot_x) < 2:
            return 0.0
        limit = 1000
        x = np.array(self.plot_x[-limit:])
        y = np.array(self.plot_y[-limit:])
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        return m

    def update_stability_status(self):
        trend = self.find_trend()
        threshold = 0.1
        if abs(trend) < threshold:
            dpg.set_value("clock_drift_status", "stable")
            dpg.configure_item("clock_drift_status", color=(100, 255, 100))
        else:
            dpg.set_value("clock_drift_status", "not stable")
            dpg.configure_item("clock_drift_status", color=(255, 0, 0))
        return abs(trend) < threshold

    def calculate_average_drift(self):
        if len(self.plot_y) < 2:
            return 0.0
        return np.mean(np.diff(self.plot_y[-self.limit:]))

    def update_average_drift_display(self):
        avg_drift = self.calculate_average_drift()
        dpg.set_value("average_clock_drift_text", f"Average clock drift: {avg_drift:.2f} Hz")

    def update_derivative_plot(self):
        if len(self.plot_y) < 2:
            return
        derivative = np.diff(self.plot_y)
        x_deriv = self.plot_x[1:]

        dpg.configure_item("raw_drift_derivative_series",
                           x=x_deriv[-self.limit:],
                           y=derivative[-self.limit:])
        dpg.fit_axis_data("raw_drift_derivative")

    def reset_calibration(self):
        self.data_buffer = np.array([], dtype=np.float32)
        self.processed_count = 0
        self.plot_x = []
        self.plot_y = []
        dpg.configure_item("drift_series", x=[], y=[])
        dpg.configure_item("raw_drift_derivative_series", x=[], y=[])
        dpg.configure_item("clock_drift_text", "Delta = 0.0 Hz")
        dpg.configure_item("average_clock_drift_text", "Average clock drift: N/A Hz")
        dpg.configure_item("clock_drift_status", "not stable", color=(255, 0, 0))


_controller = ClockCorrectionController()


def start_calibration(sender, app_data, user_data):
    _controller.start()


def stop_calibration(sender, app_data, user_data):
    _controller.stop()


def draw_clock_correction_tab():
    with dpg.tab(label="Clock Correction"):
        with dpg.collapsing_header(label="Clock Drift Calibration", default_open=True):
            dpg.add_text("Calibrate your SDR's clock drift here.")
            dpg.add_text("Aim at a known geostationary satellite", wrap=400)
            dpg.add_listbox(label="Select Satellite", items=["USA-230", "Other"],
                            width=-1)
            dpg.add_input_float(label="Frequency (MHz)", default_value=2262.5, format="%.2f MHz")

            dpg.add_button(label="Start Calibration", tag="btn_start_calib", width=-1,
                           callback=start_calibration)

            dpg.add_text("Delta = 0.0 Hz", tag="clock_drift_text", color=(255, 200, 100))
            dpg.add_text("Average clock drift: N/A Hz", tag="average_clock_drift_text", color=(200, 200, 255))

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
