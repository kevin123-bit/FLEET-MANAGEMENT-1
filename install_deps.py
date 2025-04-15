import subprocess
import sys
import importlib.util

def install_package(package):
    if importlib.util.find_spec(package) is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = [
    'flask',
    'flask-sqlalchemy',
    'flask-login',
    'flask-migrate',
    'python-dotenv',
    'geopy',
    'werkzeug',
    'sqlalchemy',
    'pytz',
    'email-validator'
]

def main():
    print("Checking and installing required packages...")
    for package in required_packages:
        try:
            install_package(package)
            print(f"✓ {package}")
        except Exception as e:
            print(f"✗ Error installing {package}: {e}")
            sys.exit(1)
    print("\nAll packages installed successfully!")

if __name__ == "__main__":
    main()
