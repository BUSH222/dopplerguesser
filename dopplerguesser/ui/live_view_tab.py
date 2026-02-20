import dearpygui.dearpygui as dpg
import os
import threading
import time
from datetime import datetime
from dopplerguesser.script_control.runner import FlowgraphRunner
from dopplerguesser.misc.rigctl_query import query_rigctl
from dopplerguesser.misc.constants import C
from dopplerguesser.config import config

from dopplerguesser.predict.fetch_tles import fetch_tles
from dopplerguesser.predict.filters import (
    filter_visibility, filter_heo, filter_geostationary,
    filter_by_doppler, filter_constellations, filter_debris, filter_by_epoch
)
from dopplerguesser.predict.matcher import score_candidates
from dopplerguesser.predict.observer import Observer


class LiveViewController:
    def __init__(self):
        self.runner = None
        self.plot_x = []
        self.plot_y = []
        self.center_freq = 0
        self.running = False
        self.limit = 1000
        self.prediction_running = False
        self.prediction_active = False
        self.prediction_results = []
        self.prediction_candidates = []
        self.prediction_observer = None
        self.update_interval = 5
        self.fallback_sample_rate = 2e6

    def start_monitoring(self):
        if self.running:
            return

        correct_iq = dpg.get_value("chk_live_dc_spike")

        try:
            freq, sr = query_rigctl()
            self.center_freq = freq
            sample_rate = sr
            dpg.set_value("txt_center_freq", f"Central Frequency (Hz): {freq}")
        except Exception as e:
            print(f"Rigctl query failed: {e}")
            dpg.set_value("txt_center_freq", "Central Frequency (Hz): Error/Unknown")
            sample_rate = self.fallback_sample_rate

        params = {
            "s": sample_rate,
            "d": int(correct_iq)
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
        dpg.set_value("live_doppler_text", f"{current_offset:.2f} Hz")

        if self.center_freq > 0:
            v = (current_offset / self.center_freq) * C
            dpg.set_value("live_velocity_text", f"{v:.2f} m/s")

    def update_plot(self):
        if not self.plot_x:
            return

        x_data = self.plot_x[-self.limit:]
        y_data = self.plot_y[-self.limit:]

        dpg.configure_item("live_doppler_series", x=x_data, y=y_data)
        dpg.fit_axis_data("live_doppler_xaxis")
        dpg.fit_axis_data("live_doppler_yaxis")

    def clear_plot(self):
        self.plot_x = []
        self.plot_y = []
        dpg.configure_item("live_doppler_series", x=[], y=[])

    def remove_last_point(self):
        if self.plot_x:
            self.plot_x.pop()
        if self.plot_y:
            self.plot_y.pop()
        dpg.configure_item("live_doppler_series", x=self.plot_x, y=self.plot_y)

    def save_plot_data(self):
        if self.prediction_results:
            top_candidate = self.prediction_results[0][0].satellite.name
            top_candidate = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in top_candidate)
        else:
            top_candidate = "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{top_candidate}_{timestamp}_doppler_data.csv"
        first_reception_time = self.runner.first_reception_time if self.runner else 0
        with open(filename, "w") as f:
            f.write("Time(s),DopplerOffset(Hz)\n")
            for x, y in zip(self.plot_x, self.plot_y):
                absolute_time = x + first_reception_time
                f.write(f"{absolute_time},{y}\n")
        print(f"Live doppler data saved to {filename}")

    def run_prediction(self):
        if self.prediction_running:
            return

        if not self.plot_x or not self.plot_y:
            dpg.set_value("prediction_status", "Error: No data available")
            return

        if not self.center_freq:
            dpg.set_value("prediction_status", "Error: Center frequency unknown")
            return

        self.prediction_running = True
        self.prediction_active = True
        dpg.set_value("prediction_status", "Initializing prediction...")
        dpg.configure_item("btn_predict", enabled=False)
        dpg.configure_item("btn_stop_predict", enabled=True)

        thread = threading.Thread(target=self._prediction_worker, daemon=True)
        thread.start()

    def stop_prediction(self):
        if self.prediction_active:
            print("Stopping prediction loop...")
            self.prediction_active = False
            dpg.set_value("prediction_status", "Prediction stopped")
            dpg.configure_item("btn_predict", enabled=True)
            dpg.configure_item("btn_stop_predict", enabled=False)

    def _prediction_worker(self):
        try:
            if not self.plot_x:
                dpg.set_value("prediction_status", "Error: No doppler data available")
                return

            t_zero_offset = self.plot_x[0]
            prediction_t_start = self.runner.first_reception_time + t_zero_offset

            self.prediction_observer = Observer(
                lat=config["lat"],
                lon=config["lon"],
                alt=config["alt"]
            )
            print(f"Observer: {config['lat']}, {config['lon']}, {config['alt']}m")

            satellites = fetch_tles(prediction_t_start)
            print(f"Loaded {len(satellites)} satellites")

            # Filtering
            print(f"Initial candidates: {len(satellites)}")

            # Debris filter
            if config["filter_debris"]:
                satellites = filter_debris(satellites)
                print(f"After debris filter: {len(satellites)}")

            # Epoch filter
            if config["filter_by_epoch"] and config["max_tle_age_days"] > 0:
                satellites = filter_by_epoch(satellites, maxage=config["max_tle_age_days"])
                print(f"After epoch filter: {len(satellites)}")

            # Constellation filter
            if config["filter_constellations"]:
                constellations = [
                    c.strip().lower()
                    for c in config["filter_constellations_list"].split(",")
                    if c.strip()
                ]
                if constellations:
                    satellites = filter_constellations(satellites, constellations)
                    print(f"After constellation filter: {len(satellites)}")

            # Geostationary filter
            satellites = filter_geostationary(satellites)
            print(f"After geostationary filter: {len(satellites)}")

            # HEO filter
            if config["filter_heo"]:
                satellites = filter_heo(satellites)
                print(f"After HEO filter: {len(satellites)}")

            # Visibility filter
            min_elev = config["filter_visibility_min_elevation"]
            satellites = filter_visibility(
                satellites, self.prediction_observer, prediction_t_start, min_elevation=min_elev
            )
            print(f"After visibility filter: {len(satellites)}")

            if not satellites:
                print("No satellites passed filters!")
                dpg.set_value("prediction_status", "No satellites found")
                self.prediction_running = False
                self.prediction_active = False
                dpg.configure_item("btn_predict", enabled=True)
                dpg.configure_item("btn_stop_predict", enabled=False)
                return

            # Doppler filter
            if config["filter_doppler"]:
                if self.plot_x and self.plot_y:
                    first_freq = self.center_freq + self.plot_y[0]
                    threshold = config["filter_doppler_threshold"]
                    satellites = filter_by_doppler(
                        satellites, self.prediction_observer, prediction_t_start,
                        self.center_freq, first_freq, threshold=threshold
                    )
                    print(f"After Doppler filter: {len(satellites)}")

                    if not satellites:
                        print("No satellites passed Doppler filter!")
                        dpg.set_value("prediction_status", "No matches found")
                        self.prediction_running = False
                        self.prediction_active = False
                        dpg.configure_item("btn_predict", enabled=True)
                        dpg.configure_item("btn_stop_predict", enabled=False)
                        return

            # Track computation
            self.prediction_observer.compute_track(prediction_t_start, duration=config["propagation_cache_duration"])
            print("Observer track computed")

            for sat in satellites:
                sat.compute_initial_state(prediction_t_start)
            print("Satellites propagated via sgp4 to t0")

            for sat in satellites:
                sat.compute_track(prediction_t_start, duration=config["propagation_cache_duration"])
            print("Candidate tracks created and cached")

            self.prediction_candidates = satellites
            dpg.set_value("prediction_status", f"Tracking {len(satellites)} candidates...")

            # Scoring loop
            while self.prediction_active:
                measurements = [
                    (dt - t_zero_offset, self.center_freq + shift)
                    for dt, shift in zip(self.plot_x, self.plot_y)
                ]

                if not measurements:
                    time.sleep(self.update_interval)
                    continue

                scored = score_candidates(
                    self.prediction_candidates,
                    measurements,
                    self.center_freq,
                    self.prediction_observer
                )

                self.prediction_results = scored[:10]
                self._update_results_table()
                dpg.set_value(
                    "prediction_status",
                    f"Active: {len(self.prediction_candidates)} candidates, {len(measurements)} points"
                )
                time.sleep(self.update_interval)

        except Exception as e:
            print(f"Prediction error: {e}")
            dpg.set_value("prediction_status", f"Error: {str(e)}")
        finally:
            self.prediction_running = False
            self.prediction_active = False
            dpg.configure_item("btn_predict", enabled=True)
            dpg.configure_item("btn_stop_predict", enabled=False)
            print("Prediction worker thread finished.")

    def _update_results_table(self):
        for i in range(5):
            if i < len(self.prediction_results):
                sat, rmse = self.prediction_results[i]
                dpg.set_value(f"prediction_sat_{i}", sat.satellite.name)
                dpg.set_value(f"prediction_rmse_{i}", f"{rmse:.2f}")
            else:
                dpg.set_value(f"prediction_sat_{i}", "—")
                dpg.set_value(f"prediction_rmse_{i}", "—")


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
            dpg.add_checkbox(label="Remove DC Spike", tag="chk_live_dc_spike", default_value=True)

            dpg.add_spacer(height=5)
            dpg.add_text("Live Readings:")
            with dpg.group(horizontal=True):
                dpg.add_text("Doppler Offset: ")
                dpg.add_text("0.0 Hz", tag="live_doppler_text", color=(100, 255, 100))

            with dpg.group(horizontal=True):
                dpg.add_text("Rel. Velocity: ")
                dpg.add_text("0.0 m/s", tag="live_velocity_text", color=(100, 255, 255))

        with dpg.collapsing_header(label="Predict", default_open=True):
            dpg.add_text('Confirm PLL is locked and doppler readings are stable before predicting.', wrap=350)
            dpg.add_button(label="Start Predicting", width=-1, tag="btn_predict",
                           callback=lambda: _live_controller.run_prediction())
            dpg.add_button(label="Stop", width=-1, tag="btn_stop_predict",
                           callback=lambda: _live_controller.stop_prediction(), enabled=False)
            dpg.add_text("Status: Idle", tag="prediction_status", color=(200, 200, 200))

            dpg.add_separator()
            dpg.add_text("Top Candidates (RMSE):")

            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                           borders_innerV=True, borders_outerV=True, row_background=True):
                dpg.add_table_column(label="Satellite", width_stretch=True)
                dpg.add_table_column(label="RMSE (Hz)", width_fixed=True, init_width_or_weight=100)

                for i in range(5):
                    with dpg.table_row():
                        dpg.add_text("—", tag=f"prediction_sat_{i}")
                        dpg.add_text("—", tag=f"prediction_rmse_{i}")

        with dpg.collapsing_header(label="Doppler Curve", default_open=True):
            with dpg.plot(label="Doppler History", height=200, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="live_doppler_xaxis")
                with dpg.plot_axis(dpg.mvYAxis, label="Shift (Hz)", tag="live_doppler_yaxis"):
                    dpg.add_line_series([], [], label="Measured", tag="live_doppler_series")
                    dpg.add_button(label="Remove last point", width=-1, callback=_live_controller.remove_last_point)
                    dpg.add_spacer(height=5)
                    dpg.add_button(label="Clear", width=-1, callback=_live_controller.clear_plot)
                    dpg.add_button(label="Save Plot Data", width=-1,
                                   callback=_live_controller.save_plot_data)
