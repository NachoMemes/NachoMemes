import json
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Union

from dacite import from_dict
from discord import Guild

from nachomemes.guild_config import GuildConfig
from nachomemes.store import Store, get_guild_id


class LocalTemplateStore(Store):
    def __init__(self) -> None:
        """
        Local filesystem read-only data store which uses the default JSON files fron the "config/" directory. 
        """

    def refresh_memes(self, guild: Optional[GuildConfig], hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def get_template_data(
        self, guild: Optional[Guild], guild_id: str, increment_use: bool = False
    ) -> dict:
        return _load_templates(guild)[guild_id]

    def list_memes(self, guild: Union[Guild,GuildConfig,str,None] = None, fields: List[str] = None) -> Iterable[dict]:
        if fields:
            return ({k: d[k] for k in fields} for d in _load_templates(guild).values())
        else:
            return _load_templates(guild).values()

    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        return _load_config(guild)

    def save_guild_config(self, guild: GuildConfig):
        pass

    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        raise NotImplementedError("local store is read-only")


@lru_cache(maxsize=1)
def _load_config(guild: Optional[Guild]) -> GuildConfig:
    """
    Loads the default guild configuration as a GuildConfig object from JSON given the ID specified in the guild parameter.
    Loads guilds from from "config/guild.json".
    By default, the guild with a null ID is loaded as a GuildConfig with name "default" if no guild name was specified in the argument.
    """
    with open("config/guild.json", "r") as f:
        config = from_dict(GuildConfig, json.load(f))
    config.guild_id = get_guild_id(guild)
    config.name = guild.name if guild else "default"
    return config


@lru_cache(maxsize=1)
def _load_templates(guild: Union[Guild,GuildConfig,str,None]) -> Dict[str, dict]:
    """
    Loads layouts from "config/layouts.json", and uses them to populate the text box list of the templates loaded from "config/templates.json".
    """
    # load layouts
    with open("config/layouts.json", "r") as f:
        layouts = json.load(f)

    # load memes
    with open("config/templates.json", "r") as f:
        data = json.load(f)

    # add name and textbox date to template
    for name, d in data.items():
        d["textboxes"] = layouts[d["layout"]]
        d["name"] = name

    # deserialize
    return data
