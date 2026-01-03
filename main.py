import numpy as np
import matplotlib.pyplot as plt
import socket
import time

HOST = '127.0.0.1'
PORT = 12346

plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel('Sample number (averaged)')
ax.set_ylabel('Drift estimate (Hz)')
ax.legend(['Filtered Drift'])
line, = ax.plot([], [], color='red', label='Filtered Drift')
fig.show()


window_size = 100
all_data = np.array([], dtype=np.float32)
processed_samples = 0

print(f"Connecting to {HOST}:{PORT}...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Connected.")
    s.setblocking(False)

    last_update_time = time.time()

    try:
        while True:
            try:
                data_bytes = s.recv(4096)
                if data_bytes:
                    new_data = np.frombuffer(data_bytes, dtype=np.float32)
                    all_data = np.concatenate((all_data, new_data))
            except BlockingIOError:
                pass
            if time.time() - last_update_time > 5:
                if len(all_data) >= processed_samples + window_size:

                    new_chunk_to_process = all_data[processed_samples:]

                    filtered_data = np.convolve(new_chunk_to_process,
                                                np.ones(window_size)/window_size, mode='valid')

                    y_data = np.concatenate((line.get_ydata(), filtered_data))

                    line.set_xdata(np.arange(len(y_data)))
                    line.set_ydata(y_data)

                    ax.relim()
                    ax.autoscale_view()

                    processed_samples += len(filtered_data)

                last_update_time = time.time()

            fig.canvas.flush_events()
            time.sleep(0.1)

    except KeyboardInterrupt:
        fig.savefig("drift_estimate.png")
        print("Stopping...")
    finally:
        print("Connection closed.")
