#!/usr/bin/env python3
"""Simple script to check if astor is available"""

import sys

print("Python path:")
for path in sys.path:
    print(f"  - {path}")

print("\nChecking for astor:")
try:
    import astor

    print("✅ astor is available")
    print(f"astor version: {astor.__version__}")
    print(f"astor path: {astor.__file__}")
except ImportError as e:
    print(f"❌ astor is not available: {e}")
