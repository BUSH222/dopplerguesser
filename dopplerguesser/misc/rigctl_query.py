import socket


def query_rigctl(addr='localhost:4532'):
    try:
        with socket.create_connection((addr.split(':')[0], int(addr.split(':')[1])), timeout=2) as s:
            s.sendall(b'f\n')
            freq_data = s.recv(1024).decode().strip()
            s.sendall(b'm\n')  # RAW\nNUMBER
            bw_data = s.recv(1024).decode().strip().split('\n')[1]
            frequency = float(freq_data)
            bandwidth = float(bw_data)
            return frequency, bandwidth
    except Exception as e:
        print(f"Error querying rigctl: {e}")
        return None, None
