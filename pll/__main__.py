from .dpll import DPLL
from .load_samples import receive_samples
from dopplerguesser.misc.rigctl_query import query_rigctl  # return frequency, bandwidth
import time


class DPLLReceiver:
    def __init__(self, f_s):
        self.f_s = f_s
        self.dpll = DPLL(f_s=f_s, bw_hz=10000.0, f_max=f_s / 2.0)
        self.samplecount = 0
        self.starttime = None
        self.last_state = None

    def handler(self, samples):
        if not self.starttime:
            self.starttime = time.time()

        out = self.dpll.run(samples)
        if len(samples) > 0:
            self.last_state = {
                'f_est': out['f_est'][-1],
                'p_lock': out['p_lock'][-1],
                'error': out['error'][-1]
            }

        self.samplecount += len(samples)

        if time.time() - self.starttime >= 1.0:
            self.print_state()
            self.starttime = time.time()
            self.samplecount = 0

    def print_state(self):
        if self.last_state:
            print(f"[{self.samplecount} sps] "
                  f"f_est: {self.last_state['f_est']:>8.2f} Hz | "
                  f"p_lock: {self.last_state['p_lock']:>5.3f} | "
                  f"error: {self.last_state['error']:>6.3f} rad")
        else:
            print(f"Received {self.samplecount} samples")


if __name__ == "__main__":
    freq, bw = query_rigctl()
    f_s = float(bw)  # Bandwidth acts as sample rate

    print(f"Initialized DPLL Receiver with sample rate: {f_s} Hz")
    receiver = DPLLReceiver(f_s=f_s)

    # Blocks and receives
    receive_samples(receiver.handler)
