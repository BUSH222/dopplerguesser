from .dpll import DPLL
from .load_samples import receive_samples
from dopplerguesser.misc.rigctl_query import query_rigctl  # return frequency, bandwidth
import time
import numpy as np
import argparse


class DPLLReceiver:
    def __init__(self, f_s, bw_hz=1000):
        self.f_s = f_s
        self.dpll = DPLL(f_s=f_s, bw_hz=bw_hz, f_max=120e3)
        self.samplecount = 0
        self.starttime = None
        self.accumulated_f_est = []
        self.accumulated_error = []

    def handler(self, samples):
        if not self.starttime:
            self.starttime = time.time()

        out = self.dpll.run(samples)
        if len(samples) > 0:
            self.accumulated_f_est.extend(out['f_est'])
            self.accumulated_error.extend(out['error'])

        self.samplecount += len(samples)

        if time.time() - self.starttime >= 1.0:
            self.print_state()
            self.starttime = time.time()
            self.samplecount = 0
            self.accumulated_f_est = []
            self.accumulated_error = []

    def print_state(self):
        if self.accumulated_f_est:
            avg_f_est = np.mean(self.accumulated_f_est)
            avg_error = np.mean(self.accumulated_error)
            print(f"[{self.samplecount} sps] "
                  f"f_est (avg): {avg_f_est:>8.2f} Hz | "
                  f"error (avg): {avg_error:>6.3f} rad")
        else:
            print(f"Received {self.samplecount} samples")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DPLL Receiver.")
    parser.add_argument("--bw", type=float, default=500, help="PLL Bandwidth in Hz")
    parser.add_argument("--sample_rate", type=float, help="Sample rate")
    args = parser.parse_args()
    if args.sample_rate:
        f_s = args.sample_rate
        bw = f_s
    else:
        freq, bw = query_rigctl()
        f_s = float(bw)

    print(f"Initialized DPLL Receiver with sample rate: {f_s} Hz")
    receiver = DPLLReceiver(f_s=f_s, bw_hz=args.bw)

    # Blocks and receives
    receive_samples(receiver.handler, port=12345, sample_format='cs16')
