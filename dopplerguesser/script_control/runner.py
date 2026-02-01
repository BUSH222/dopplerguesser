import subprocess
import threading
import socket
import time
import numpy as np
import os
from dopplerguesser.config import config


class FlowgraphRunner:
    def __init__(self, script_path, host='127.0.0.1', port=12346, params=None):
        self.script_path = script_path
        self.host = host
        self.port = port
        self.params = params if params else {}
        self.process = None
        self._running = False
        self._thread = None
        self.on_data = None
        self.first_reception_time = None

    def start(self, on_data_callback=None):
        if self._running:
            print("FlowgraphRunner is already running.")
            return

        self.on_data = on_data_callback
        self.first_reception_time = None

        python_exec = config.get('gr_path')
        if not python_exec or not os.path.exists(python_exec):
            python_exec = "python3"

        if not os.path.exists(self.script_path):
            print(f"Error: Script not found at {self.script_path}")
            return

        cmd = [python_exec, self.script_path]
        for key, value in self.params.items():
            cmd.append(f"-{key}")
            cmd.append(str(value))
        print(f"Launching flowgraph: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(cmd)
            self._running = True
        except Exception as e:
            print(f"Failed to start subprocess: {e}")
            return

        self._thread = threading.Thread(target=self._monitor_stream, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the flowgraph process and the monitor thread."""
        self._running = False
        if self.process:
            if self.process.poll() is None:
                print("Terminating flowgraph process...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Force killing process...")
                    self.process.kill()
            self.process = None

        if self._thread and self._thread.is_alive():
            pass
        print("Flowgraph runner stopped.")

    def is_running(self):
        return self._running and (self.process is not None) and (self.process.poll() is None)

    def _monitor_stream(self):
        """Internal method to handle socket connection and data streaming."""
        time.sleep(5)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)

        connected = False
        attempts = 0
        while not connected and attempts < 5 and self._running:
            try:
                sock.connect((self.host, self.port))
                sock.setblocking(False)
                connected = True
                print(f"Connected to flowgraph socket at {self.host}:{self.port}")
            except (ConnectionRefusedError, socket.timeout):
                if not self._running:
                    break
                time.sleep(1)
                attempts += 1

        if not connected:
            print("Failed to connect to flowgraph socket after retries.")
            if self._running:
                pass
            sock.close()
            return

        current_bin = 0
        current_buffer = []

        while self._running:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                now = time.time()
                if self.first_reception_time is None:
                    self.first_reception_time = now

                relative_time = now - self.first_reception_time
                bin_index = int(relative_time + 0.5)
                data = np.frombuffer(chunk, dtype=np.float32)
                if bin_index > current_bin:
                    if current_buffer:
                        avg_val = float(np.mean(current_buffer))
                        if self.on_data:
                            self.on_data([(current_bin, avg_val)])
                    current_buffer = []
                    current_bin = bin_index
                current_buffer.extend(data)

            except BlockingIOError:
                time.sleep(0.01)
            except Exception as e:
                print(f"Socket stream error: {e}")
                break

        sock.close()
        print("Socket monitor thread finished.")
