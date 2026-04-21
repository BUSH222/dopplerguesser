import numpy as np


class NCO:
    def __init__(self, f_s: float, f_center: float = 0.0, f_max: float = None):
        self.f_s = f_s
        self.f_center = f_center
        self.theta = 0.0
        self.dphi0 = 2 * np.pi * f_center / f_s
        self.dphi_max = 2 * np.pi * abs(f_max - f_center) / f_s if f_max is not None else np.pi

    def update_limits(self, f_max: float):
        self.dphi_max = 2 * np.pi * abs(f_max - self.f_center) / self.f_s

    @property
    def frequency(self) -> float:
        return self.theta / (2 * np.pi) * self.f_s
