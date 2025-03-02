import sys
import subprocess
import importlib.util

required_packages = ['requests', 'pandas', 'numpy', 'tradingview-ta']

for package in required_packages:
    spec = importlib.util.find_spec(package)
    if spec is None:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} installed successfully")
    else:
        print(f"{package} is already installed")