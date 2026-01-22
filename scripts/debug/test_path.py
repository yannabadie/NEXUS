#!/usr/bin/env python3
from pathlib import Path

# Test on Windows
path = Path('/etc/passwd')
print(f'Path: {path}')
print(f'is_absolute(): {path.is_absolute()}')
print(f'starts with /: {str(path).startswith("/")}')