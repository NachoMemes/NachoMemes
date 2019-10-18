import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Type, Union

from discord import Member, Role, Guild
from dacite import Config, from_dict

from store import MemeTemplate, Store, da_config, GuildConfig, guild_id


class LocalTemplateStore(Store):
    def __init__(self):
        pass

    def refresh_memes(self, guild: Union[str, int, Guild], hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def read_meme(
        self, guild: Union[str, int, Guild], id: str, increment_use: bool = False
    ) -> MemeTemplate:
        return _load_templates(guild)[id]

    def list_memes(self, guild: Union[str, int, Guild], fields: List[str] = None) -> Iterable[dict]:
        result = (asdict(t) for t in _load_templates(guild_id(guild)).values())
        if fields:
            result = ({k: d[k] for k in fields} for d in result)
        return result

    def guild_config(self, guild: Guild) -> GuildConfig:
        return _load_config(guild)

    def save_guild_config(self, guild: GuildConfig):
        pass


@lru_cache(maxsize=1)
def _load_config(guild: Guild) -> GuildConfig:
    with open("config/guild.json", "r") as f:
        config = from_dict(GuildConfig, json.load(f))
    config.id = str(guild.id)
    config.name = guild.name
    return config

@lru_cache(maxsize=1)
def _load_templates(guild: Union[str, int, Guild]) -> Iterable[MemeTemplate]:

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
