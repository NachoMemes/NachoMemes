#!/usr/bin/env python

"""
Script to automate the running of the bot.
Handles debug mode and the store to run the bot with.
Debug will run with test credentials and in verbose error mode.
Local will run the bot with a local store that uses the filesystem instead of DynamoDB.
"""

import argparse
import subprocess
from .bot import run

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
    run(args.debug, args.local)
