import os
import sys

# Add parent directory (backend) to sys.path to support both "app.*" and "backend.app.*" imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
