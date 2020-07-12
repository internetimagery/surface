import sys

if sys.version_info[0] < 3:
    raise RuntimeError("Python 3+ is required to compare API.")