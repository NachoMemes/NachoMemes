#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
Script to automate the running of the bot.
Handles the branch, debug and refresh state to run the bot in.
Debug means it will run with test credentials and in verbose error mode.
Refresh means it will HARD pull the branch you've chosen and run from there.
"""

import argparse
import subprocess

def main(debug=False, local=False):
    """
    Builds and runs a list of processes.
    """

    base_command = "python3 -m nachomemes.bot"
    if debug:
        base_command = base_command + " --debug"
    if local:
        base_command = base_command + " --local"

    subprocess.call([base_command], shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs the bot with the passed in arguments."
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Run state::debug. True or false. Runs different credentials and logging level.",
    )

    parser.add_argument(
        "-l", "--local", action="store_true", help="Run locally without DynamoDB."
    )

    args = parser.parse_args()
    main(args.debug, args.local)
