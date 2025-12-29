import numpy as np
import matplotlib.pyplot as plt

data = np.fromfile("clock_drift_out.txt", dtype=np.float32)[30:]  # low values in ppl estimator
print(data[0:10])
window_size = 1000
filtered_data = np.convolve(data, np.ones(window_size)/window_size, mode='valid')

plt.plot(filtered_data, color='red', label='Data 1')
plt.xlabel('Sample number (averaged)')
plt.ylabel('drift estimate (Hz)')
plt.legend()
plt.savefig("out.png")
plt.show()
