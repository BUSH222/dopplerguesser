from .loop_filter import LoopFilter
from .numerically_controlled_oscillator import NCO
import numpy as np
import math

from ._dpll_ext import run_dpll_loop  # type: ignore
# if this ^ raises an error,
# run python setup.py build_ext --inplace
# to compile the C++ extension before using this module


class DPLL:

    def __init__(self, f_s: float, bw_hz: float, f_max: float,
                 f_center: float = 0.0, zeta: float = 0.707,
                 use_fft_freq_find: bool = True, fft_freq_find_timeout: float = 1.0):
        self.f_s = f_s
        self.f_center = f_center
        self.f_max = f_max

        # FFT Freq Find
        self.use_fft_freq_find = use_fft_freq_find
        self.fft_freq_find_timeout = fft_freq_find_timeout
        self._fft_buffer = []
        self._samples_collected = 0
        self._samples_to_collect = int(self.f_s * self.fft_freq_find_timeout)
        self._decimation_factor = max(1, int(self.f_s / (2 * self.f_max)))
        self._fft_done = not use_fft_freq_find

        # Loop filter
        self._zeta = zeta
        self._bw = bw_hz
        self.loop_filter = LoopFilter(f_s=f_s, bw_hz=bw_hz, zeta=zeta)

        # NCO
        self.nco = NCO(f_s=f_s, f_center=f_center, f_max=f_max)

        # self.output_buffer = []

    def _find_optimal_fft_size(self, sample_length: int) -> int:
        return 2**math.floor(math.log2(sample_length))

    def set_bandwidth(self, bw_hz: float):
        self._bw = bw_hz
        self.loop_filter.update_params(self.f_s, bw_hz, self._zeta)

    def set_f_max(self, f_max: float):
        self.nco.update_limits(f_max)

    def handler(self, samples: np.ndarray):
        self.run(samples)
        # self.output_buffer.append(out)

    def run(self, samples: np.ndarray) -> dict:
        """Process a block of complex samples. Returns arrays of outputs."""
        if not self._fft_done:
            self._fft_buffer.append(samples[::self._decimation_factor])
            self._samples_collected += len(samples)

            if self._samples_collected >= self._samples_to_collect:
                fft_in = np.concatenate(self._fft_buffer)
                fft_size = self._find_optimal_fft_size(len(fft_in))
                print(f"FFT Size: {fft_size}")
                fft_in = fft_in[:fft_size]

                spectrum = np.abs(np.fft.fftshift(np.fft.fft(fft_in)))
                fs_dec = self.f_s / self._decimation_factor
                freqs = np.fft.fftshift(np.fft.fftfreq(fft_size, d=1/fs_dec))

                self.f_center = freqs[np.argmax(spectrum)]
                print(f"FFT estimate: {self.f_center:.2f} Hz")
                self.nco.f_center = self.f_center
                self.nco.dphi0 = 2 * np.pi * self.f_center / self.f_s
                self.nco.update_limits(self.f_max)

                self._fft_done = True
                self._fft_buffer.clear()

            return {
                'error': np.array([]),
                'f_est': np.array([]),
                'nco': np.array([]),
            }

        errors, f_ests, nco_vals, nco_theta, lf_int = run_dpll_loop(
            samples,
            self.nco.theta,
            self.nco.dphi0,
            self.nco.dphi_max,
            self.loop_filter.integrator,
            self.loop_filter.K1,
            self.loop_filter.K2,
            self.f_s,
            self.f_center
        )

        self.nco.theta = nco_theta
        self.loop_filter.integrator = lf_int

        return {
            'error': errors,
            'f_est': f_ests,
            'nco': nco_vals,
        }
