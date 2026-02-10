# Dopplerguesser
**An application that determines what satellite you are receiving based on the doppler signature of its signal.**

It is designed to work in conjunction with [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus), a cross-platform and open source SDR software. 
> Note: If you are using MacOS, the IQ exporter module vital for this application to work is missing from the official builds. Download SDR++ from my [fork](https://github.com/BUSH222/SDRPlusPlus) instead.

## Table of Contents

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

## Usage

## Algorithm

## License
[MIT License](LICENSE)

## Acknowledgements

## References
