import os, json

from .guild_config import GuildConfig
from .template import Template, TemplateError
from .store import Store, da_config, guild_id
from .dynamo_store import DynamoTemplateStore
from .local_store import LocalTemplateStore
from .render import render_template


def get_store(local: bool=True, debug: bool=True) -> Store:
    creds = get_creds(debug) if not local else {}
    store: Store = LocalTemplateStore()
    if not local and "access_key" in creds:
        store = DynamoTemplateStore(
            creds["access_key"], creds["secret"], creds["region"], store, debug
        )    
    return store


def get_creds(debug: bool=True) -> dict:
    try:
        creds_file_name = (
            "/config/creds.json" if not debug else "/config/testing-creds.json"
        )
        with open(os.getcwd() + creds_file_name, "r") as f:
            creds: dict = json.load(f)
    except:
        creds = {}
    for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
        if k in os.environ:
            creds[k.lower()] = os.environ[k]
    return creds

