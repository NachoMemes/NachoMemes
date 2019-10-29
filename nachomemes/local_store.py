import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Type, Union, Optional

from discord import Member, Role, Guild
from dacite import Config, from_dict

from .guild_config import GuildConfig
from .store import MemeTemplate, Store, da_config, guild_id


class LocalTemplateStore(Store):
    def __init__(self):
        pass

    def refresh_memes(self, guild: Optional[Guild], hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def read_meme(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> MemeTemplate:
        return _load_templates(guild)[id]

    def list_memes(self, guild: Optional[Guild], fields: List[str] = None) -> Iterable[dict]:
        result = (asdict(t) for t in _load_templates(guild).values())
        if fields:
            result = ({k: d[k] for k in fields} for d in result)
        return result

    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        return _load_config(guild)

    def save_guild_config(self, guild: GuildConfig):
        pass

    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        raise NotImplementedError("local store is read-only")


@lru_cache(maxsize=1)
def _load_config(guild: Optional[Guild]) -> GuildConfig:
    with open("config/guild.json", "r") as f:
        config = from_dict(GuildConfig, json.load(f))
    config.id = guild_id(guild)
    config.name = guild.name if guild else "default"
    return config

@lru_cache(maxsize=1)
def _load_templates(guild: Optional[Guild]) -> Iterable[MemeTemplate]:

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
    return {k: from_dict(MemeTemplate, v, config=da_config) for k, v in data.items()}
