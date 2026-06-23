"""Convenience launcher.

Run either:
    python main.py
or:
    python -m megaufobot.main
"""

import runpy

if __name__ == "__main__":
    runpy.run_module("megaufobot.main", run_name="__main__")
