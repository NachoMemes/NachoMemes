#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Script to automate the running of the bot.
Handles the branch, debug and refresh state to run the bot in.
Debug means it will run with test credentials and in verbose error mode. 
Refresh means it will HARD pull the branch you've chosen and run from there.
"""

import argparse
import os
import subprocess
import sys


def main(branch=None, debug=False, refresh=False, local=False):
    """ Builds and runs a list of processes.
    """
    runCommand = "python3 bot.py"
    if debug:
        runCommand = runCommand + " --debug"
    if local:
        runCommand = runCommand + " --local"
    
    if branch:
        for c in ("git reset HEAD --hard",
                   "git fetch",
                   "git checkout {branch}",
                   "git pull" 
                ):
                if c == "git reset HEAD --hard" and refresh == false:
                    continue
                subprocess.call([c], shell=True)
    subprocess.call([runCommand], shell=True)



if __name__ == "__main__":
    # Setup and define the arg parser.
    # This is so that we can take command line input.
    parser = argparse.ArgumentParser(
        description="Runs the bot passed on input parameters."
    )
    parser.add_argument(
        "-b",
        "--branch",
        type=str, 
        action="store", 
        help="Optional. Which branch the bot should be run from."
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Run state::debug. True or false. Runs different credentials and logging level.",
    )

    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        help="Whether or not to pull fresh from the branch",
    )

    parser.add_argument(
        "-l",
        "--local", 
        action="store_true", 
        help="Run locally without DynamoDB."
    )

    args = parser.parse_args()
    main(args.branch, args.debug, args.refresh, args.local)
