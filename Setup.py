import subprocess
import sys


def install_packages():
    packages = ['selenium', 'webdriver-manager']
    return subprocess.run([sys.executable, '-m', 'pip', 'install', *packages], check=False).returncode


if __name__ == '__main__':
    raise SystemExit(install_packages())