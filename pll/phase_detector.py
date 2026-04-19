from numpy import angle, conj


def phase_detector(x_n: complex, nco_n: complex):
    """arctan phase detector"""
    return angle(x_n * conj(nco_n))


def phase_detector_cross(x_n: complex, nco_n: complex) -> float:
    """cross product phase detector"""
    dot = x_n.real * nco_n.real + x_n.imag * nco_n.imag
    cross = x_n.real * nco_n.imag - x_n.imag * nco_n.real
    mag = max(abs(dot), 1e-9)
    return cross / mag
