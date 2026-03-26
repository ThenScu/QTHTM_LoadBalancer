#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup and requirements installer
"""

import subprocess
import sys


def install_requirements():
    """Cài đặt Python requirements"""
    packages = [
        "requests",
    ]
    
    print("Installing Python packages...")
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("All packages installed successfully!")


if __name__ == "__main__":
    install_requirements()
