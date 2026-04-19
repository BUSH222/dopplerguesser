import numpy as np
import socket
import time


def receive_samples(handler, host='localhost', port=12345, chunk_size=1024):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        buffer = bytearray()
        while True:
            data = s.recv(chunk_size)
            if not data:
                break
            buffer.extend(data)

            bytes_to_process = (len(buffer) // 4) * 4
            if bytes_to_process > 0:
                raw_bytes = buffer[:bytes_to_process]
                del buffer[:bytes_to_process]

                raw = np.frombuffer(raw_bytes, dtype=np.int16)
                iq = raw.astype(np.float32)
                complex_samples = (iq[0::2] + 1j * iq[1::2]) / 32768.0

                handler(complex_samples)


def load_samples_from_file(file_path, handler, chunk_size=1024):
    # cs16 only for now
    with open(file_path, 'rb') as f:
        while True:
            raw_bytes = f.read(chunk_size * 4)
            if not raw_bytes:
                break

            raw = np.frombuffer(raw_bytes, dtype=np.int16)
            iq = raw.astype(np.float32)
            complex_samples = (iq[0::2] + 1j * iq[1::2]) / 32768.0

            handler(complex_samples)


class MockSampleReceiver():
    def __init__(self):
        self.samplecount = 0
        self.starttime = None
        pass

    def handler(self, samples):
        if not self.starttime:
            self.starttime = time.time()
        if time.time() - self.starttime >= 1.0:
            self.print_sample_speed()
            self.starttime = time.time()
            self.samplecount = 0
        self.samplecount += len(samples)

    def print_sample_speed(self):
        if self.starttime:
            elapsed = time.time() - self.starttime
            if elapsed > 0:
                print(f"Received {self.samplecount/elapsed:.0f} samples/second)")
        else:
            print(f"Received {self.samplecount} samples")


if __name__ == "__main__":
    mock_receiver = MockSampleReceiver()
    receive_samples(mock_receiver.handler)
