# Dopplerguesser
**An application that determines what satellite you are receiving based on the doppler signature of its signal.**

It is designed to work in conjunction with [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus), a cross-platform and open source SDR software. 
> Note: If you are using MacOS, the IQ exporter module vital for this application to work is missing from the official builds. Build from source or download SDR++ from my [fork](https://github.com/BUSH222/SDRPlusPlus) instead.

## Table of Contents
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation-1)
  - [Initial Configuration](#initial-configuration)
  - [SDR++ Configuration](#sdr-configuration)
- [Usage](#usage)
  - [Result Interpretation](#result-interpretation)
  - [Debugging](#debugging)
- [Algorithm](#algorithm)
  - [1. Signal Processing](#1-signal-processing)
  - [2. Frequency to Relative Speed](#2-frequency-to-relative-speed)
  - [3. Observer and Satellite Position Propagation](#3-observer-and-satellite-position-propagation)
  - [4. Candidate Selection](#4-candidate-selection)
  - [5. Candidate Scoring](#5-candidate-scoring)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [References](#references)

## Installation
>The application has been tested exclusively on MacOS, so issues may appear when using this on Linux, and especially Windows. Please report them in issues

### Prerequisites
- [Python 3.13+](https://www.python.org/downloads/)
- GNURadio installed from [radioconda](https://github.com/radioconda/radioconda-installer) (Planned to be phased out from this project soon)

### Installation
1) Clone this repository:  
`git clone https://github.com/BUSH222/dopplerguesser`
2) Navigate to the project root using `cd /path/to/dopplerguesser` and create a virtual environment using `python3 -m venv venv` (or `python -m venv venv` on Windows)
3) Activate the venv using `source /venv/bin/activate` on MacOS/Linux (or `venv\Scripts\activate` on Windows)
4) Install the required packages: `pip install -r requirements.txt`
5) Start the application using `python3 main.py`

### Initial Configuration
1) Navigate to the settings tab in the application.
2) In the `Observer Location` tab, set your position (latitude, longitude, and altitude)
3) In the `Connections` tab, set the python path created by radioconda (likely different from python executing this application). On MacOS, the default is /Users/username/radioconda/bin/python. This path can be found when executing any GNURadio script from the companion.
4) Save the settings

### SDR++ Configuration
1) Enable the `iq_exporter` and `rigctl_server` modules in the module manager. If IQ Exporter is missing on MacOS, you will instead need to build sdr++ from source, or download it from my [fork](https://github.com/BUSH222/SDRPlusPlus).
2) Disable the `radio` module
3) Configure IQ Exporter: set mode to VFO, samplerate to 2-6 MS/s, Protocol to TCP (Server), sample type to Int16, Packet size to 1024, host to localhost, port to 12345. Start the IQ Exporter.
4) Configure Rigctl server: set host to localhost, port to 4532, controlled VFO to IQ Exporter, check tuning and listen on startup, and start.

## Usage
> This program should work at or below 2300MHz. It has been tested on S- and L- band satellite signals.

The program is tall and narrow on purpose to fit nicely along SDR++ in split view like this:
![Example Usage](readme_materials/exampleusage.png)
> Always update TLEs before use! TLEs are valid for a week at most, and their precision is constantly going down. The fresher the TLEs, the better the precision of the app.
1) Identify a continuous signal exhibiting doppler shift
2) Move IQ Exporter's VFO to roughly around the signal. 
> Tuning tip: Doppler shift from LEO satellites makes the frequency go down over time, so tune a bit lower than the frequency.
3) With IQ Exporter and Rigctl server running in SDR++, click `Connect` in the live view tab of the application. After ~5 seconds the frequency readings will start appearing in the Doppler History graph.
4) Wait for the PLL to lock onto the signal. The stronger and closer to 0 it is, the faster it will lock. The lock will be signified by a sharp peak (or drop) followed by a slowly descending plateau.
5) Once locked, clear the irrelevant pll locking data by pressing the clear button.
6) Click `Start Predicting` and after some time look at the table. It will show the top predicted candidates for the transmission. The longer you track the satellite, the bigger the confidence will be.
7) After the satellite signal gets too weak, click the `Disconnect` button and trim the last points using `remove last point` button if necessary. You can now judge whether the prediction was successful or not and save the plot data for further processing.

The data you saved can be processed manually and used in the `Processing` tab.

### Result interpretation
Look at the top candidates table. It shows the top 5 candidates and their RMSE (root mean squared error). It is a number that shows how much on average the predicted values differ from the observed values. The lower it is the better the match.

RMSE <= 50: Perfect match, the prediction is very likely correct.\
50 < RMSE <= 300: Good match, TLE may be slightly out of date. Check the epoch to confirm.\
RMSE > 300: Bad match, the prediction is wrong or you have not updated TLEs for a long time.


> When the program correctly predicted a satellite, the difference in RMSE between the first and second candidate is often very large, over 1000Hz for long passes.

### Debugging
Several factors might contribute to the results being nonsensical.
#### Clock drift
A good clock on the receiver side is essential for this application to work. A TCXO works, but an OCXO or a GPSDO are advised for better precision. 
> Note about TCXOs: Though they are temperature compensated, shifts in temperature still affect them. Using the application while the clock is cooling down or warming up is not advised.

To check if your clock is suitable:
1. Tune to a known geostationary satellite signal or other stable reference signal (these have no Doppler shift)
2. Enable the Clock Correction tab and click "Start Calibration"
3. Wait for the PLL to lock (status will change from "Unlocked" to "Locked")
4. Monitor the "Average clock drift" and "Current slope" values
5. Check that the clock status shows "stable" (slope < 0.1 Hz/s)

The calibration works by measuring the apparent frequency offset of a signal that should have zero Doppler shift. Any observed offset is attributed to clock drift in your receiver.

#### TLE age
Always update TLEs before starting an observation. TLEs get old and imprecise very quickly, leading to big errors between predicted and observed data.

#### Classified TLEs
The Celestrak API is not perfect: it omits some TLEs, such as, for example, the TLEs for the NOSS-3 series satellites. Manually add their TLEs and run the .csv through the processing tab.


## Algorithm
This section will describe the algorithmic approach used in this application. 

### 1. Signal processing
The signal processing in this project is done with GNURadio, using the PLL Frequency Detector block. Here is the flowgraph:
![Flowgraph](readme_materials/flowgraph.png)
The flowgraph accepts 2 parameters: sample rate and whether to remove the DC spike or not. The source of this flowgraph is a TCP Source which is directly connected to the IQ Exporter in SDR++. It outputs int16, or "short" samples which are converted and scaled to complex float 32. The data then gets throttled, and the DC spike gets removed if the parameter was specified (Important for the HackRF, for example, where the PLL keeps locking onto the DC spike even with another signal present). Then comes the PLL Frequency Detector, which is running a phase locked loop with the following parameters:

$$ Loop\ bandwidth = \frac{\pi}{10000}, \quad \omega_{\text{max}} = \frac{2\pi \cdot f_{\text{max-doppler}}}{f_s}, \quad \omega_{\text{min}} = \frac{-2\pi \cdot f_{\text{max-doppler}}}{f_s} $$

The max doppler in this case is 70KHz, which allows for operation on S-band and below. Future versions of this program will have configurable max doppler bounds and the loop bandwidth.

The PLL output is converted from normalized frequency to Hz:

$$ f_{\text{doppler}}(t) = \frac{\omega_{\text{PLL}}(t) \cdot f_s}{2\pi} $$

The signal is smoothed using a moving average filter with window size $N = 1000$ samples, then decimated to produce approximately $N$ measurements per second. These measurements are fed into a TCP Sink which enables the connection with the main application.

The main application averages the data even more: It collects all the incoming data every second and separates it into bins. All observations coming in at $[N-0.5, N+0.5)$, where N is an integer corresponding to a unix timestamp, get averaged to eliminate most of the drift in the PLL.

### 2. Frequency to relative speed
The classic doppler shift formula is defined as

$$f_{obs} = \frac{c + v_0}{c - v_s} \cdot f_{sat}$$

However, this formula is cumbersome to use, so let's simplify a bit:

$$\frac{f_{obs}}{f_{sat}} = \frac{c + v_0}{c - v_s}$$

$$\frac{f_{obs}}{f_{sat}} = \frac{c(1 + v_0/c)}{c(1 - v_s/c)} = \frac{1 + v_0/c}{1 - v_s/c}= (1 + v_0/c)(1 - v_s/c)^{-1}$$

This can be expressed through the binomial expansion for $(1 + v_s/c)^{-1}$:

$$(1 - v_s/c)^{-1} = 1 + v_s/c + (v_s/c)^2 + (v_s/c)^3 + ...$$

After multiplying, expanding up to second order and grouping by order:

$$\frac{f_{obs}}{f_{sat}} = (1 + v_0/c)(1 + v_s/c + (v_s/c)^2 + ...) = \\ 1 + v_s/c + (v_s/c)^2 + v_0/c + v_0 v_s/c^2 + ...= \\ 1 + \frac{v_0 + v_s}{c} + \frac{v_s^2 + v_0 v_s}{c^2} + ...$$

We can define the relative velocity and determine that it is much less than the speed of light for earth satellite applications: $v_{rel} = v_0+v_s << c$.

> Note: Worst case scenario relative velocity here would not exceed $1.2\times10^4$ m/s (earth escape velocity + rotation at equator) compared to the speed of light at $3\times10^8$ m/s

Keeping only the first two terms we get:

$$\frac{f_{obs}}{f_{sat}} \approx 1 + \frac{v_{rel}}{c}$$

or:

$$\boxed{v_{rel} \approx \left(\frac{f_{obs}}{f_{sat}} - 1\right) \cdot c}$$

#### Approximation error estimation:

The term we dropped is: 

$$\frac{v_s^2 + v_0 v_s}{c^2} = \frac{v_s(v_s + v_0)}{c^2} = \frac{v_s \cdot v_{rel}}{c^2}$$

Assuming the worst case scenario at $v_{rel}=1.2\times10^4$ m/s and $v_{sat}=1.12\times10^4$ m/s:

$$\text{Error} \approx \frac{1.12*10^4 \times 1.2*10^4}{(3 \times 10^8)^2} \approx 1.5 \times 10^{-9}$$

As an example, at 2.25 GHz, the maximum expected doppler shift in our worst case scenario with the normal formula is 87484Hz, but with our approximation it is 87487Hz. An error of 3 Hz is acceptable and negligible for this application. The error caused by relativistic effects can also be ignored as the speeds are small enough for it to not matter.

### 3. Observer and Satellite position propagation
#### Satellite
This project gets the orbital elements from [Celestrak's API](https://celestrak.org/NORAD/elements/) as TLEs meant to be propagated using SGP4. However, propagating to every observed point is computationally expensive, especially for many targets at once. This is why a different approach was needed.

This project propagates using SGP4 (using skyfield) to only one point - the observation start $t_0$. 

$$ \mathbf{r}_{\text{sat}}(t_0), \mathbf{v}_{\text{sat}}(t_0) = \text{SGP4}(\text{TLE}, t_0) $$

After this, the orbit is propagated using F&G functions

$$ \mathbf{r}(t + \Delta t) = f \mathbf{r}(t) + g \mathbf{v}(t) $$

$$ \mathbf{v}(t + \Delta t) = \dot{f} \mathbf{r}(t) + \dot{g} \mathbf{v}(t) $$

where the coefficients are computed by solving Kepler's equation via Newton-Raphson iteration:

$$n\Delta t =\Delta E - (1 - \frac{r_0}{a})\sin(\Delta E) + \frac{\mathbf{r}_0 \cdot \mathbf{v}_0}{\sqrt{\mu a}}(1 - \cos(\Delta E))$$

with $a$ being the semi-major axis, $n = \sqrt{\mu/a^3}$ the mean motion, and $\mu = 3.986004418 \times 10^5 km^3/s^2$ the Earth's gravitational parameter.

#### Observer
The calculation of the Observer's position is similar in approach: It calculates one precise value, accounting for Earth's gyroscopic precession and nutation using skyfield, and then simply rotates the earth for all other points: 


The GCRS position at time $t = t_0 + \Delta t$ is:

$$ \mathbf{r}_{\text{obs}}(t) = \mathbf{R}_z(\omega_{\oplus} \Delta t) \mathbf{R}_{\text{ITRS}\to\text{GCRS}}(t_0) \mathbf{r}_{\text{ITRS}} $$

where $\omega_{\oplus} = 7.2921150 \times 10^{-5}$ rad/s is Earth's rotation rate, and the observer velocity is:

$$ \mathbf{v}_{\text{obs}} = \boldsymbol{\omega}_{\oplus} \times \mathbf{r}_{\text{obs}} = \begin{bmatrix} -\omega_{\oplus} y \\ \omega_{\oplus} x \\ 0 \end{bmatrix} $$

All the simplified models can be replaced with more precise but computationally intensive models in the processing tab, but it usually does not yield better results.
### 4. Candidate selection
The Celestrak API currently provides 15000 TLEs for different satellites. Even with all the optimizations described above, propagating all these TLEs will take way too long. So, to reduce computational load some filters are applied. All of these filters are toggleable in application settings.

1. **Geostationary Filter:** Reject satellites with $n < 6$ revolutions per day. This project focuses on LEO and MEO satellites, with clearly observable doppler shift over short periods of time to mitigate the SDR receiver's clock drifting.
2. **HEO Filter:** Reject satellites with eccentricity $e > 0.25$ (optional)
3. **Visibility Filter:** Require elevation angle at $t_0$ $\theta_{\text{el}} > \theta_{\text{min}}$ (default 0°)
4. **Constellation Filter:** Exclude specified mega-constellations (e.g., Starlink, OneWeb). This filter alone eliminates 2/3 of the satellites provided by Celestrak.
5. **Doppler Pre-filter:** Reject if $|\Delta f_{\text{predicted}}(t_0) - \Delta f_{\text{observed}}(t_0)| > \epsilon$ (default threshold $\epsilon = 10000$ Hz). This helps eliminate descending satellites when the target is ascending, for example. However, if the tuning is imprecise this filter can accidentally cut the target.

### 5. Candidate Scoring

For each candidate satellite passing the filters, the algorithm computes predicted Doppler shifts at all measurement times and scores the match using normalized Root Mean Square Error (RMSE).

**Normalization:**
To account for unknown transmitter frequency and the transmitter and receiver clock drift, both observed and predicted frequencies are mean-centered:

$$ \tilde{f}_{\text{obs},i} = f_{\text{obs},i} - \bar{f}_{\text{obs}} $$

$$ \tilde{f}_{\text{pred},i} = f_{\text{pred},i} - \bar{f}_{\text{pred}} $$

**RMSE Calculation:**

$$ \text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^{N} (\tilde{f}_{\text{obs},i} - \tilde{f}_{\text{pred},i})^2} $$

Candidates are ranked by ascending RMSE. The top candidate is the most likely match.

## License
[MIT License](LICENSE)

## Acknowledgements

This project relies on several excellent tools and libraries:

- [Skyfield](https://rhodesmill.org/skyfield/) - Elegant astronomy library for satellite position computation and coordinate transformations
- [SGP4](https://pypi.org/project/sgp4/) - Python implementation of the SGP4 satellite propagation algorithm
- [GNU Radio](https://www.gnuradio.org/) - Software defined radio framework for signal processing
- [DearPyGui](https://github.com/hoffstadt/DearPyGui) - Fast and powerful Python GUI framework
- [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus) - Cross-platform SDR software
- [CelesTrak](https://celestrak.org/) - Comprehensive source of orbital element data maintained by Dr. T.S. Kelso

Special thanks to the amateur radio and satellite reception communities for their invaluable resources and knowledge sharing.


## References
todo