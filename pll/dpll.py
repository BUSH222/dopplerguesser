from .estimate_frequency import estimated_frequency
from .loop_filter import LoopFilter
from .numerically_controlled_oscillator import NCO
from .phase_detector import phase_detector
import numpy as np


class DPLL:

    def __init__(self, f_s: float, bw_hz: float, f_max: float,
                 f_center: float = 0.0, zeta: float = 0.707):
        self.f_s = f_s
        self.f_center = f_center

        # Loop filter
        self._zeta = zeta
        self._bw = bw_hz
        self.loop_filter = LoopFilter(f_s=f_s, bw_hz=bw_hz, zeta=zeta)

        # NCO
        self.nco = NCO(f_s=f_s, f_center=f_center, f_max=f_max)

        # Lock detector
        tau = 10.0 / bw_hz
        self._beta = np.exp(-1.0 / (f_s * tau))
        self._sigma2 = 0.0
        self._LOCK_THRESH = (np.pi / 6) ** 2

        # self.output_buffer = []

    def set_bandwidth(self, bw_hz: float):
        self._bw = bw_hz
        self.loop_filter.update_params(self.f_s, bw_hz, self._zeta)
        tau = 10.0 / bw_hz
        self._beta = np.exp(-1.0 / (self.f_s * tau))

    def set_f_max(self, f_max: float):
        self.nco.update_limits(f_max)

    def handler(self, samples: np.ndarray):
        self.run(samples)
        # self.output_buffer.append(out)

    def step(self, x: complex) -> dict:
        # 1. NCO
        nco_val = np.exp(1j * self.nco.theta)

        # 2. Phase detector
        phi_e = phase_detector(x, nco_val)

        # 3. Loop filter
        v = self.loop_filter.step(phi_e)

        # 4. Clamp and advance NCO
        self.nco.step(v)

        # 5. Frequency estimate
        f_est = estimated_frequency(self.f_center, self.loop_filter.integrator, self.f_s)

        # 6. Lock detection
        self._sigma2 = self._beta * self._sigma2 + (1 - self._beta) * phi_e ** 2
        p_lock = float(np.exp(-self._sigma2 / self._LOCK_THRESH))

        return {
            'nco': nco_val,
            'error': phi_e,
            'f_est': f_est,
            'p_lock': p_lock,
            'sigma2': self._sigma2,
        }

    def run(self, samples: np.ndarray) -> dict:
        """Process a block of complex samples. Returns arrays of outputs."""
        N = len(samples)
        out = {k: np.zeros(N, dtype=np.float32) for k in ('error', 'f_est', 'p_lock', 'sigma2')}
        out['nco'] = np.zeros(N, dtype=np.complex64)

        for i, x in enumerate(samples):
            r = self.step(x)
            for k in out:
                out[k][i] = r[k]
        return out
