import dearpygui.dearpygui as dpg
import os
import threading
import csv
from dopplerguesser.config import config

from dopplerguesser.predict.fetch_tles import fetch_tles
from dopplerguesser.predict.filters import (
    filter_visibility, filter_heo, filter_geostationary,
    filter_by_doppler, filter_constellations
)
from dopplerguesser.predict.matcher import score_candidates
from dopplerguesser.predict.observer import Observer


class ProcessingViewController:
    def __init__(self):
        self.plot_x = []
        self.plot_y = []
        self.center_freq = 0
        self.prediction_running = False
        self.prediction_results = []
        self.prediction_candidates = []
        self.prediction_observer = None
        self.csv_data_loaded = False

    def load_csv_data(self):
        """Load doppler data from CSV file."""
        csv_path = dpg.get_value("processing_input_csv")
        if not csv_path or not os.path.exists(csv_path):
            dpg.set_value("processing_status", "Error: Invalid CSV file path")
            return False

        try:
            center_freq_mhz_str = dpg.get_value("processing_central_freq")
            if not center_freq_mhz_str:
                dpg.set_value("processing_status", "Error: Center frequency required")
                return False

            self.center_freq = float(center_freq_mhz_str) * 1e6

            self.plot_x = []
            self.plot_y = []

            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    time_val = float(row['Time(s)'])
                    doppler_val = float(row['DopplerOffset(Hz)'])
                    self.plot_x.append(time_val)
                    self.plot_y.append(doppler_val)

            if not self.plot_x:
                dpg.set_value("processing_status", "Error: No data in CSV file")
                return False

            dpg.configure_item("processing_doppler_series", x=self.plot_x, y=self.plot_y)
            dpg.fit_axis_data("processing_doppler_xaxis")
            dpg.fit_axis_data("processing_doppler_yaxis")

            self.csv_data_loaded = True
            dpg.set_value("processing_status", f"Loaded {len(self.plot_x)} data points from CSV")
            print(f"Loaded {len(self.plot_x)} data points from {csv_path}")
            return True

        except Exception as e:
            dpg.set_value("processing_status", f"Error loading CSV: {str(e)}")
            print(f"Error loading CSV: {e}")
            return False

    def run_prediction(self):
        """Run prediction on loaded CSV data."""
        if self.prediction_running:
            dpg.set_value("processing_status", "Prediction already running")
            return

        if not self.csv_data_loaded or not self.plot_x or not self.plot_y:
            if not self.load_csv_data():
                return

        if not self.center_freq:
            dpg.set_value("processing_status", "Error: Center frequency unknown")
            return

        self.prediction_running = True
        dpg.set_value("processing_status", "Running prediction...")
        dpg.configure_item("btn_predict_processing", enabled=False)

        thread = threading.Thread(target=self._prediction_worker, daemon=True)
        thread.start()

    def _prediction_worker(self):
        """Worker thread for prediction."""
        try:
            prediction_t_start = self.plot_x[0]
            self.prediction_observer = Observer(
                lat=config["lat"],
                lon=config["lon"],
                alt=config["alt"]
            )
            print(f"Observer: {config['lat']}, {config['lon']}, {config['alt']}m")

            dpg.set_value("processing_status", "Fetching TLEs...")
            satellites = fetch_tles(prediction_t_start)
            print(f"Loaded {len(satellites)} satellites")

            dpg.set_value("processing_status", "Applying filters...")
            print(f"Initial candidates: {len(satellites)}")

            if config["filter_constellations"]:
                constellations = [
                    c.strip().lower()
                    for c in config["filter_constellations_list"].split(",")
                    if c.strip()
                ]
                if constellations:
                    satellites = filter_constellations(satellites, constellations)
                    print(f"After constellation filter: {len(satellites)}")

            satellites = filter_geostationary(satellites)
            print(f"After geostationary filter: {len(satellites)}")

            if config["filter_heo"]:
                satellites = filter_heo(satellites)
                print(f"After HEO filter: {len(satellites)}")

            min_elev = config["filter_visibility_min_elevation"]
            satellites = filter_visibility(
                satellites, self.prediction_observer, prediction_t_start, min_elevation=min_elev
            )
            print(f"After visibility filter: {len(satellites)}")

            if not satellites:
                print("No satellites passed filters!")
                dpg.set_value("processing_status", "No satellites found after filtering")
                self.prediction_running = False
                dpg.configure_item("btn_predict_processing", enabled=True)
                return

            if config["filter_doppler"]:
                first_freq = self.center_freq + self.plot_y[0]
                threshold = config["filter_doppler_threshold"]
                satellites = filter_by_doppler(
                    satellites, self.prediction_observer, prediction_t_start,
                    self.center_freq, first_freq, threshold=threshold
                )
                print(f"After Doppler filter: {len(satellites)}")

                if not satellites:
                    print("No satellites passed Doppler filter!")
                    dpg.set_value("processing_status", "No matches found after Doppler filtering")
                    self.prediction_running = False
                    dpg.configure_item("btn_predict_processing", enabled=True)
                    return

            dpg.set_value("processing_status", f"Computing tracks for {len(satellites)} candidates...")
            self.prediction_observer.compute_track(prediction_t_start, duration=config["propagation_cache_duration"])
            print("Observer track computed")

            for sat in satellites:
                sat.compute_initial_state(prediction_t_start)
            print("Satellites propagated via sgp4 to t0")

            for sat in satellites:
                sat.compute_track(prediction_t_start, duration=config["propagation_cache_duration"])
            print("Candidate tracks created and cached")

            self.prediction_candidates = satellites

            t_zero = self.plot_x[0]
            measurements = [
                (t - t_zero, self.center_freq + doppler)
                for t, doppler in zip(self.plot_x, self.plot_y)
            ]

            dpg.set_value("processing_status", f"Scoring {len(satellites)} candidates...")
            scored = score_candidates(
                self.prediction_candidates,
                measurements,
                self.center_freq,
                self.prediction_observer
            )

            self.prediction_results = scored[:10]
            self._update_results_table()

            dpg.set_value(
                "processing_status",
                f"Complete: Top candidate is {scored[0][0].satellite.name} (RMSE: {scored[0][1]:.2f} Hz)"
            )
            print(f"Prediction complete. Top candidate: {scored[0][0].satellite.name}")

        except Exception as e:
            print(f"Prediction error: {e}")
            dpg.set_value("processing_status", f"Error: {str(e)}")
        finally:
            self.prediction_running = False
            dpg.configure_item("btn_predict_processing", enabled=True)
            print("Prediction worker thread finished.")

    def _update_results_table(self):
        """Update the results table with top candidates."""
        for i in range(5):
            if i < len(self.prediction_results):
                sat, rmse = self.prediction_results[i]
                dpg.set_value(f"prediction_sat_processing_{i}", sat.satellite.name)
                dpg.set_value(f"prediction_rmse_processing_{i}", f"{rmse:.2f}")
            else:
                dpg.set_value(f"prediction_sat_processing_{i}", "—")
                dpg.set_value(f"prediction_rmse_processing_{i}", "—")

    def clear_data(self):
        """Clear loaded data and reset UI."""
        self.plot_x = []
        self.plot_y = []
        self.csv_data_loaded = False
        self.prediction_results = []
        dpg.configure_item("processing_doppler_series", x=[], y=[])
        dpg.set_value("processing_status", "Data cleared")
        for i in range(5):
            dpg.set_value(f"prediction_sat_processing_{i}", "—")
            dpg.set_value(f"prediction_rmse_processing_{i}", "—")


_processing_controller = ProcessingViewController()


def draw_processing_tab():
    with dpg.tab(label="Processing"):
        dpg.add_text("Process the .csv files generated by the live view tab here.", wrap=350)
        with dpg.collapsing_header(label="TLEs", default_open=True):
            dpg.add_checkbox(label="Use internal TLEs", default_value=True)  # TODO
            dpg.add_text("If unchecked, you can load TLEs from a file instead:")  # TODO
            dpg.add_input_text(default_value="", width=-1, enabled=False)  # TODO
        with dpg.collapsing_header(label="Processing Options", default_open=True):
            dpg.add_checkbox(label="Use precise propagation (slower)", tag="processing_precise_propagation",
                             default_value=False)  # TODO
            dpg.add_text("Central frequency (Mhz)")
            dpg.add_input_text(tag="processing_central_freq", width=-1)
            dpg.add_text("Input CSV file path")
            dpg.add_input_text(tag="processing_input_csv", default_value="", width=-1)
            dpg.add_spacer()
            dpg.add_button(label="Load CSV Data", width=-1,
                           callback=lambda: _processing_controller.load_csv_data())
            dpg.add_button(label="Clear Data", width=-1,
                           callback=lambda: _processing_controller.clear_data())
            dpg.add_spacer()

        with dpg.collapsing_header(label="Results", default_open=True):
            dpg.add_button(label="Predict", width=-1, tag="btn_predict_processing",
                           callback=lambda: _processing_controller.run_prediction())
            dpg.add_text("Status: Idle", tag="processing_status", color=(200, 200, 200))
            dpg.add_text("Top Candidates (RMSE):")

            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                           borders_innerV=True, borders_outerV=True, row_background=True):
                dpg.add_table_column(label="Satellite", width_stretch=True)
                dpg.add_table_column(label="RMSE (Hz)", width_fixed=True, init_width_or_weight=100)

                for i in range(5):
                    with dpg.table_row():
                        dpg.add_text("—", tag=f"prediction_sat_processing_{i}")
                        dpg.add_text("—", tag=f"prediction_rmse_processing_{i}")

        with dpg.collapsing_header(label="Doppler Curve", default_open=True):
            with dpg.plot(label="Doppler History", height=200, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="processing_doppler_xaxis")
                with dpg.plot_axis(dpg.mvYAxis, label="Shift (Hz)", tag="processing_doppler_yaxis"):
                    dpg.add_line_series([], [], label="Measured", tag="processing_doppler_series")
