"""These are Nacho Memes"""
import os
import json
import argparse

from .guild_config import GuildConfig
from .template import Template, TemplateError
from .store import Store, da_config, get_guild_id
from .dynamo_store import DynamoTemplateStore
from .local_store import LocalTemplateStore
from .render import render_template

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Runs the bot with the passed in arguments."
    )

    parser.add_argument("-d", "--debug", action="store_true",
        help="Run state::debug. True or false. Runs different credentials and logging level.")

    parser.add_argument(
        "-l", "--local", action="store_true", help="Run locally without DynamoDB.")

    return parser.parse_args()

def get_store(local: bool=True, debug: bool=True) -> Store:
    """
    Intializes and returns a store based on whether local is set.
    If "access_key" doesn't exist in the JSON config file, defaults to the local store.
    """
    creds = get_creds(debug) if not local else {}
    store: Store = LocalTemplateStore()
    if not local and "access_key" in creds:
        store = DynamoTemplateStore(
            creds["access_key"], creds["secret"], creds["region"], store, debug
        )
    return store


def get_creds(debug: bool=True) -> dict:
    """
    Gets credentails as a dict from JSON configuration files in the config/ directory.
    Environment variables override JSON configuration values.
    """
    try:
        creds_file_name = (
            "/config/creds.json" if not debug else "/config/testing-creds.json"
        )
        with open(os.getcwd() + creds_file_name, "r") as file:
            creds = json.load(file)
    except OSError:
        creds = {}
    for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
        if k in os.environ:
            creds[k.lower()] = os.environ[k]
    return creds
