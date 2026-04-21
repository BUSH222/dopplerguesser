import numpy as np
import socket


def receive_samples(handler, host='localhost', port=12345, chunk_size=2**15):
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
