import dearpygui.dearpygui as dpg
import threading
import socket
import time
import numpy as np
import os
from dopplerguesser.script_control import runner


_calibration_state = {
    "running": False,
    "process": None,
    "thread": None,
    "data_buffer": np.array([], dtype=np.float32),
    "processed_count": 0,
    "plot_x": [],
    "plot_y": [],
    "host": '127.0.0.1',
    "port": 12346,
    "window_size": 100
}


def _calibration_task():
    state = _calibration_state
    time.sleep(5)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            try:
                s.connect((state["host"], state["port"]))
                s.setblocking(False)
                print("Connected to GNURadio flowgraph.")
            except Exception as e:
                print(f"Connection failed: {e}")
                _stop_calibration_internal()
                return

            last_update_time = time.time()

            while state["running"]:
                try:
                    data_bytes = s.recv(4096)
                    if data_bytes:
                        new_data = np.frombuffer(data_bytes, dtype=np.float32)
                        state["data_buffer"] = np.concatenate((state["data_buffer"], new_data))

                        if len(new_data) > 0:
                            dpg.set_value("clock_drift_text", f"Current Drift: {new_data[-1]:.2f} Hz")

                except BlockingIOError:
                    pass
                except Exception as e:
                    print(f"Socket error: {e}")
                    break

                if time.time() - last_update_time > 0.2:
                    if len(state["data_buffer"]) >= state["processed_count"] + state["window_size"]:

                        chunk = state["data_buffer"][state["processed_count"]:]
                        window = np.ones(state["window_size"]) / state["window_size"]
                        filtered = np.convolve(chunk, window, mode='valid')

                        current_len = len(state["plot_y"])
                        new_len = len(filtered)
                        new_x = np.arange(current_len, current_len + new_len)

                        state["plot_x"].extend(new_x.tolist())
                        state["plot_y"].extend(filtered.tolist())
                        state["processed_count"] += new_len

                        limit = 1000
                        dpg.configure_item("drift_series", x=state["plot_x"][-limit:], y=state["plot_y"][-limit:])
                        dpg.fit_axis_data("drift_x_axis")
                        dpg.fit_axis_data("drift_y_axis")

                    last_update_time = time.time()

                time.sleep(0.01)

    except Exception as e:
        print(f"Calibration thread error: {e}")
    finally:
        print("Calibration thread exited.")


def _stop_calibration_internal():
    state = _calibration_state
    state["running"] = False

    if state["process"]:
        runner.stop_flowgraph(state["process"])
        state["process"] = None
    dpg.configure_item("btn_start_calib", label="Start Calibration", callback=start_calibration)


def start_calibration(sender=None, app_data=None, user_data=None):
    state = _calibration_state
    if state["running"]:
        return

    script_path = os.path.abspath(os.path.join("gr_scripts", "pll_lock.py"))
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        dpg.set_value("clock_drift_text", f"Error: Script not found at {script_path}")
        return

    print(f"Starting flowgraph: {script_path}")
    state["process"] = runner.run_flowgraph(script_path)
    state["running"] = True

    state["data_buffer"] = np.array([], dtype=np.float32)
    state["processed_count"] = 0
    state["plot_x"] = []
    state["plot_y"] = []

    dpg.configure_item("drift_series", x=[], y=[])
    dpg.configure_item("btn_start_calib", label="Stop Calibration", callback=stop_calibration)

    state["thread"] = threading.Thread(target=_calibration_task, daemon=True)
    state["thread"].start()


def stop_calibration(sender=None, app_data=None, user_data=None):
    _stop_calibration_internal()


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

            dpg.add_text("Current Drift: 0.0 Hz", tag="clock_drift_text", color=(255, 200, 100))
            with dpg.collapsing_header(label="Drift History", default_open=False):
                with dpg.plot(label="Drift History", height=300, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Sample", tag="drift_x_axis")
                    with dpg.plot_axis(dpg.mvYAxis, label="Drift (Hz)", tag="drift_y_axis"):
                        dpg.add_line_series([], [], label="Filtered Drift", tag="drift_series")
