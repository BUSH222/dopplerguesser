class LoopFilter:
    def __init__(self, f_s: float, bw_hz: float, zeta: float = 0.707):
        self.update_params(f_s, bw_hz, zeta)
        self.integrator = 0.0

    def update_params(self, f_s: float, bw_hz: float, zeta: float):
        T = 1.0 / f_s
        omega_n = bw_hz / (zeta + 1.0 / (4.0 * zeta))
        self.K1 = 2.0 * zeta * omega_n * T
        self.K2 = (omega_n * T) ** 2
