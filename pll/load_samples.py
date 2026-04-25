import numpy as np
import socket
import threading
import queue


def receive_samples(handler, host='localhost', port=12345, chunk_size_bytes=2**17, num_buffers=8):
    chunk_size_bytes = (chunk_size_bytes // 4) * 4

    free_queue = queue.Queue(maxsize=num_buffers)
    ready_queue = queue.Queue(maxsize=num_buffers)

    for _ in range(num_buffers):
        free_queue.put(bytearray(chunk_size_bytes))

    def producer():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            while True:
                try:
                    buf = free_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                view = memoryview(buf)
                bytes_received = 0

                while bytes_received < chunk_size_bytes:
                    try:
                        n = s.recv_into(view[bytes_received:])
                        if not n:
                            break
                        bytes_received += n
                    except Exception:
                        break

                if bytes_received == 0:
                    ready_queue.put(None)
                    break

                ready_queue.put((buf, bytes_received))

                if bytes_received < chunk_size_bytes:
                    ready_queue.put(None)  # Signal EOF
                    break

    t = threading.Thread(target=producer, daemon=True)
    t.start()

    try:
        while True:
            item = ready_queue.get()
            if item is None:
                break

            buf, bytes_valid = item

            samples_valid = bytes_valid // 4
            if samples_valid > 0:
                raw_bytes = memoryview(buf)[:samples_valid * 4]
                raw = np.frombuffer(raw_bytes, dtype=np.int16)
                complex_samples = raw.astype(np.float32).view(np.complex64)
                complex_samples /= 32768.0

                handler(complex_samples)

            free_queue.put(buf)

    except KeyboardInterrupt:
        pass


def load_samples_from_file(file_path, handler, chunk_size=1024):
    # cs16 only for now
    with open(file_path, 'rb') as f:
        while True:
            raw_bytes = f.read(chunk_size * 4)
            if not raw_bytes:
                break

            raw = np.frombuffer(raw_bytes, dtype=np.int16)
            complex_samples = raw.astype(np.float32).view(np.complex64)
            complex_samples /= 32768.0

            handler(complex_samples)
