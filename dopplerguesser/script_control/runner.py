import threading
import time
import numpy as np
from dopplerguesser.config import config  # noqa: F401
from pll.dpll import DPLL
from pll.load_samples import receive_samples


class DPLLRunner:
    """
    Runner for managing DPLL execution and data streaming.

    Args:
        host (str): The host address to connect to (default: '127.0.0.1').
        port (int): The port to connect to (default: 12345).
        params (dict, optional): Configuration parameters. Supported keys:
            - 's' (int): Sample rate (default: 192000).
            - 'bw' (int): Bandwidth in Hz (default: 900).
            - 'sample_format' (str): Sample format (default: 'cs16').
    """
    def __init__(self, host='127.0.0.1', port=12345, params=None):
        self.host = host
        self.port = port
        self.params = params if params else {}
        self._running = False
        self._thread = None
        self.on_data = None
        self.first_reception_time = None
        self.dpll = None
        self.stop_event = threading.Event()

        self.current_bin = 0
        self.current_buffer = []

    def start(self, on_data_callback=None):
        if self._running:
            print("DPLLRunner is already running.")
            return

        self.on_data = on_data_callback
        self.first_reception_time = None
        self.current_bin = 0
        self.current_buffer = []
        self.stop_event.clear()

        sample_rate = self.params.get('s', 192000)
        bw_hz = self.params.get('bw', 900)

        self.dpll = DPLL(f_s=sample_rate, bw_hz=bw_hz, f_max=120e3)

        self._running = True
        self._thread = threading.Thread(target=self._monitor_stream, daemon=True)
        self._thread.start()

    def dpll_data_handler(self, samples):
        if not self._running:
            return

        now = time.time()
        if self.first_reception_time is None:
            self.first_reception_time = now

        out = self.dpll.run(samples)
        f_ests = out['f_est']

        relative_time = now - self.first_reception_time
        bin_index = int(relative_time + 0.5)

        if bin_index > self.current_bin:
            if self.current_buffer:
                avg_val = float(np.mean(self.current_buffer))
                if self.on_data:
                    self.on_data([(self.current_bin, avg_val)])
            self.current_buffer = []
            self.current_bin = bin_index

        self.current_buffer.extend(f_ests)

    def stop(self):
        """Stops the dpll process and the monitor thread."""
        self._running = False
        self.stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        print("DPLL runner stopped.")

    def is_running(self):
        return self._running

    def _monitor_stream(self):
        """Internal method to handle socket connection and data streaming via DPLL."""
        print(f"Connecting to to sdr++ at {self.host}:{self.port}")

        sample_format = self.params.get('sample_format', 'cs16')

        receive_samples(
            handler=self.dpll_data_handler,
            host=self.host,
            port=self.port,
            sample_format=sample_format,
            stop_event=self.stop_event
        )

        self._running = False
        print("Socket monitor thread finished.")
