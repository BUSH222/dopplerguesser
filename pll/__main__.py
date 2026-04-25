from .dpll import DPLL
from .load_samples import receive_samples
from dopplerguesser.misc.rigctl_query import query_rigctl  # return frequency, bandwidth
import time
import numpy as np


class DPLLReceiver:
    def __init__(self, f_s):
        self.f_s = f_s
        self.dpll = DPLL(f_s=f_s, bw_hz=1000, f_max=120e3)
        self.samplecount = 0
        self.starttime = None
        self.accumulated_f_est = []
        self.accumulated_p_lock = []
        self.accumulated_error = []

    def handler(self, samples):
        if not self.starttime:
            self.starttime = time.time()

        out = self.dpll.run(samples)
        if len(samples) > 0:
            self.accumulated_f_est.extend(out['f_est'])
            self.accumulated_p_lock.extend(out['p_lock'])
            self.accumulated_error.extend(out['error'])

        self.samplecount += len(samples)

        if time.time() - self.starttime >= 1.0:
            self.print_state()
            self.starttime = time.time()
            self.samplecount = 0
            self.accumulated_f_est = []
            self.accumulated_p_lock = []
            self.accumulated_error = []

    def print_state(self):
        if self.accumulated_f_est:
            avg_f_est = np.mean(self.accumulated_f_est)
            avg_p_lock = np.mean(self.accumulated_p_lock)
            avg_error = np.mean(self.accumulated_error)
            print(f"[{self.samplecount} sps] "
                  f"f_est (avg): {avg_f_est:>8.2f} Hz | "
                  f"p_lock (avg): {avg_p_lock:>5.3f} | "
                  f"error (avg): {avg_error:>6.3f} rad")
        else:
            print(f"Received {self.samplecount} samples")


if __name__ == "__main__":
    freq, bw = query_rigctl()
    f_s = float(bw)

    print(f"Initialized DPLL Receiver with sample rate: {f_s} Hz")
    receiver = DPLLReceiver(f_s=f_s)

    # Blocks and receives
    receive_samples(receiver.handler)
