import subprocess
from dopplerguesser.config import ConfigManager


def run_flowgraph(script_path):
    """Run the GNURadio flowgraph script located at script_path."""
    config = ConfigManager()
    process = subprocess.Popen([config.python_executable, script_path])
    return process


def stop_flowgraph(process):
    """Terminate the GNURadio flowgraph process."""
    if process:
        process.terminate()
        process.wait()
        print("Flowgraph process terminated.")


def is_flowgraph_running(process):
    """Check if the GNURadio flowgraph process is still running."""
    return process and (process.poll() is None)
