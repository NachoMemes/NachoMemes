import os, sys, json, asyncio
from argparse import ArgumentParser
from collections import OrderedDict
from warnings import warn
from typing import Any, List, Optional

from discord import Client

from nachomemes import Store, LocalTemplateStore, DynamoTemplateStore, Uploader, DiscordChannelUploader

class Configuration:
    _uploader: Uploader
    _store: Store

    def __init__(self, args: Optional[List[str]] = None):
        parser = ArgumentParser(
            description="Runs the bot with the passed in arguments."
        )
        parser.add_argument("-d", "--debug", action="store_true",
            help="Run state::debug. True or false. Runs different credentials and logging level.")
        parser.add_argument("-l", "--local", action="store_true",
            help="Run locally without DynamoDB.")
        self.config = parser.parse_args(args)

        creds_file_name = os.getcwd() + (
            "/config/creds.json" if not self.config.debug else "/config/testing-creds.json"
        )
        try:
            with open(creds_file_name, "r") as file:
                creds = json.load(file)
                self.config.__dict__.update(creds)
        except OSError:
            warn("no credendials found in " + creds_file_name)
        for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
            if k in os.environ:
                setattr(self.config, k.lower(), os.environ[k])


    @property
    def store(self) -> Store:
        if not self._store:
            self._store = LocalTemplateStore()
            if not self.local and self.access_key:
                self._store = DynamoTemplateStore(
                    self.access_key, self.secret, self.region, self._store, self.debug
                )
        return self._store

    @property
    def uploader(self) -> Uploader:
        if not self._uploader:
            self._uploader = DiscordChannelUploader(self._discord_client, 825517179326824498)
        return self._uploader

    @property
    def discord_client(self) -> Client:
        return self._discord_client

    @discord_client.setter
    def discord_client(self, client: Client) -> None:
        # asyncio.get_event_loop().run_until_complete(client.login(self.discord_token))
        self._discord_client = client

    def start_discord_client(self) -> None:
        self._discord_client.run(self.discord_token)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.config, attr, None)

