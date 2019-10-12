import json
from functools import lru_cache
from typing import Callable, Iterable, List, Dict, Any, Type
from dataclasses import asdict

from dacite import from_dict, Config

from store import Store, MemeTemplate, da_config


class LocalTemplateStore(Store):
    def __init__(self):
        pass

    def refresh_memes(self, guild: str, hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def read_meme(
        self, guild: str, id: str, increment_use: bool = False
    ) -> MemeTemplate:
        return _load(guild)[id]

    def list_memes(self, guild: str, fields: List[str] = None) -> Iterable[dict]:
        result = (asdict(t) for t in _load(guild).values())
        if fields:
            result = ({k: d[k] for k in fields} for d in result)
        return result

    def guild_config(self, guild: str) -> dict:
        pass


@lru_cache(maxsize=1)
def _load(guild: str) -> Iterable[MemeTemplate]:

    # load layouts
    with open("config/layouts.json", "r") as f:
        layouts = json.load(f)

    # load memes
    with open("config/templates.json", "r") as f:
        data = json.load(f)

    # add name and textbox date to template
    for name, d in data.items():
        d['textboxes'] = layouts[d['layout']]
        d['name'] = name


    # deserialize
    return { k: from_dict(MemeTemplate, v, config=da_config) for k,v in data.items() }

