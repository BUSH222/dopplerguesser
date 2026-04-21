#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/complex.h>
#include <cmath>
#include <complex>

namespace py = pybind11;

std::tuple<py::array_t<float>, py::array_t<float>, py::array_t<float>, py::array_t<float>, py::array_t<std::complex<float>>, float, float, float>
run_dpll_loop(py::array_t<std::complex<float>> samples, 
             float nco_theta, float dphi0, float dphi_max, 
             float lf_integrator, float K1, float K2, 
             float f_s, float f_center, 
             float beta, float sigma2, float LOCK_THRESH) 
{
    py::buffer_info buf = samples.request();
    int N = buf.size;
    
    auto x_ptr = static_cast<std::complex<float>*>(buf.ptr);

    // Output arrays
    auto errors = py::array_t<float>(N);
    auto f_ests = py::array_t<float>(N);
    auto p_locks = py::array_t<float>(N);
    auto sigma2s = py::array_t<float>(N);
    auto nco_vals = py::array_t<std::complex<float>>(N);

    auto err_ptr = static_cast<float*>(errors.request().ptr);
    auto fest_ptr = static_cast<float*>(f_ests.request().ptr);
    auto plock_ptr = static_cast<float*>(p_locks.request().ptr);
    auto sig_ptr = static_cast<float*>(sigma2s.request().ptr);
    auto nco_ptr = static_cast<std::complex<float>*>(nco_vals.request().ptr);

    const float twopi = 2.0f * M_PI;

    for (int i = 0; i < N; ++i) {
        std::complex<float> x = x_ptr[i];

        // 1. Phase detector
        float phi_e = std::arg(x) - nco_theta;
        while (phi_e > M_PI) phi_e -= twopi;
        while (phi_e < -M_PI) phi_e += twopi;

        // 2. NCO val (to output)
        std::complex<float> nco_val(std::cos(nco_theta), std::sin(nco_theta));

        // 3. Loop filter
        lf_integrator += K2 * phi_e;
        float v = K1 * phi_e + lf_integrator;

        // 4. Clamp and advance NCO
        float v_clamped = std::max(-dphi_max, std::min(dphi_max, v));
        nco_theta += dphi0 + v_clamped;
        while (nco_theta > M_PI) nco_theta -= twopi;
        while (nco_theta < -M_PI) nco_theta += twopi;

        // 5. Frequency estimate
        float f_est = f_center + lf_integrator * f_s / twopi;

        // 6. Lock detection
        sigma2 = beta * sigma2 + (1.0f - beta) * (phi_e * phi_e);
        float p_lock = sigma2;

        err_ptr[i] = phi_e;
        fest_ptr[i] = f_est;
        plock_ptr[i] = p_lock;
        sig_ptr[i] = sigma2;
        nco_ptr[i] = nco_val;
    }

    return std::make_tuple(errors, f_ests, p_locks, sigma2s, nco_vals, nco_theta, lf_integrator, sigma2);
}

PYBIND11_MODULE(_dpll_ext, m) {
    m.doc() = "C++ extension for DPLL core loop";
    m.def("run_dpll_loop", &run_dpll_loop, "Run the core DPLL computations loop");
}
