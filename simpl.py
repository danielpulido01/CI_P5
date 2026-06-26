#!/usr/bin/env python3
# simpl.py — SimPL interpreter entry point.

import sys
import os

# Make sure the package directory is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simpl.shell import Shell

def main():
    shell = Shell()

    # Load any files given on the command line before entering the REPL
    for filename in sys.argv[1:]:
        shell.load(filename)

    shell.run()

if __name__ == '__main__':
    main()
