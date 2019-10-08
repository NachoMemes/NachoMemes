#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Script to automate the running of the bot.
Handles the branch, debug and refresh state to run the bot in.
Debug means it will run with test credentials and in verbose error mode. 
Refresh means it will HARD pull the branch you've chosen and run from there.
"""

import argparse
import os
import sys
import subprocess


def main(branch, debug=False, refresh=False):
    """ Builds and runs a list of processes.
    """
    commands = [
        "git reset HEAD --hard",
        "git fetch",
        f"git checkout {branch}",
        "git pull",
        f"python bot.py {debug}",
    ]
    if not refresh:
        commands.pop(0)
    for proc in commands:
        subprocess.call([proc], shell=True)


if __name__ == "__main__":
    # Setup and define the arg parser.
    # This is so that we can take command line input.
    parser = argparse.ArgumentParser(
        description="Runs the bot passed on input parameters."
    )
    parser.add_argument(
        "branch", metavar="b", type=str, help="Which branch the bot should be run from."
    )
    parser.add_argument(
        "--debug",
        metavar="d",
        type=bool,
        default=False,
        help="Run state::debug. True or false. Runs different credentials and logging level.",
    )

    parser.add_argument(
        "--refresh",
        metavar="r",
        type=bool,
        help="Whether or not to pull fresh from the branch",
    )

    args = parser.parse_args()

    main(args.branch, args.debug, args.refresh)

