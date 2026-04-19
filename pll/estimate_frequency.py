from numpy import pi


def estimated_frequency(f_center, integrator_state, f_s):
    return f_center + integrator_state * f_s / (2 * pi)
