#!/usr/bin/env python
# Run provided command if in python 3 else do nothing
import sys
if sys.version_info.major < 3:
    print("Not in python 3. Not running commands.")
    sys.exit(0)
import subprocess
sys.exit(subprocess.run(sys.argv[1:]).returncode)
