from .loop_filter import LoopFilter
from .numerically_controlled_oscillator import NCO
import numpy as np

try:
    from ._dpll_ext import run_dpll_loop  # type: ignore
    HAS_EXT = True
except ImportError:
    HAS_EXT = False

assert HAS_EXT


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

    def run(self, samples: np.ndarray) -> dict:
        """Process a block of complex samples. Returns arrays of outputs."""
        errors, f_ests, sigma2s_raw, sigma2s, nco_vals, nco_theta, lf_int, sigma2_out = run_dpll_loop(
            samples.astype(np.complex64),
            self.nco.theta,
            self.nco.dphi0,
            self.nco.dphi_max,
            self.loop_filter.integrator,
            self.loop_filter.K1,
            self.loop_filter.K2,
            self.f_s,
            self.f_center,
            self._beta,
            self._sigma2,
            self._LOCK_THRESH
        )

        p_locks = np.exp(-sigma2s_raw / self._LOCK_THRESH)

        self.nco.theta = nco_theta
        self.loop_filter.integrator = lf_int
        self._sigma2 = sigma2_out

        return {
            'error': errors,
            'f_est': f_ests,
            'p_lock': p_locks,
            'sigma2': sigma2s,
            'nco': nco_vals,
        }
