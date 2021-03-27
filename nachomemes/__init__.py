"""These are Nacho Memes"""
import os, sys, json
from argparse import ArgumentParser
from collections import OrderedDict
from typing import Any, List, Optional

from .guild_config import GuildConfig
from .template import Template, TemplateError
from .store import Store, da_config, get_guild_id
from .dynamo_store import DynamoTemplateStore
from .local_store import LocalTemplateStore
from .render import render_template
from .uploader import Uploader

class Configuration:
    def __init__(self, args: Optional[List[str]] = None):
        parser = ArgumentParser(
            description="Runs the bot with the passed in arguments."
        )
        parser.add_argument("-d", "--debug", action="store_true",
            help="Run state::debug. True or false. Runs different credentials and logging level.")
        parser.add_argument("-l", "--local", action="store_true",
            help="Run locally without DynamoDB.")
        self.config = parser.parse_args(args)

        try:
            creds_file_name = (
                "/config/creds.json" if not self.config.debug else "/config/testing-creds.json"
            )
            with open(os.getcwd() + creds_file_name, "r") as file:
                self.config.__dict__.update(json.load(file))
        except OSError:
            pass
        for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
            if k in os.environ:
                setattr(self.config, k.lower(), os.environ[k])

        self.config.store = LocalTemplateStore()
        if not self.config.local and self.config.access_key:
            self.config.store = DynamoTemplateStore(
                self.config.access_key, self.config.secret, self.config.region, self.config.store, self.config.debug
            )

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.config, attr)

class SimpleCache(OrderedDict):
    def __init__(self, max_items:int):
        self.max_items = max_items;

    def __setitem__ (self, key, new_value):
        if len(self) > self.max_items:
            self.popitem(last=False)
        super().__setitem__(key, new_value)

