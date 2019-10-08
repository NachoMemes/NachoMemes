import json
from typing import Callable, Iterable, List
from functools import lru_cache

from render import MemeTemplate, TextBox
from store import Store

class LocalTemplateStore(Store):
    def __init__(self):
        pass

    def refresh_memes(self, guild: str, hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def read_meme(self, guild: str, id: str, increment_use: bool = False) -> MemeTemplate:
        return self._load()[id]

    def list_memes(self, guild: str, fields: List[str]=None) -> Iterable[dict]:
        result = (t.serialize() for t in self._load().values())
        if fields:
            result = ({k:d[k] for k in fields} for d in result)
        return result

    def guild_config(self, guild: str) -> dict:
        pass

    @lru_cache(maxsize=1)
    def _load(guild: str) -> Iterable[MemeTemplate]:
        # load meme layouts
        with open("config/layouts.json", "rb") as t:
            layouts = json.load(
                t, object_hook=lambda d: TextBox.deserialize(d) if "face" in d else d
            )

        # load memes
        with open("config/templates.json", "rb") as t:
            memes = json.load(
                t,
                object_hook=lambda d: MemeTemplate.deserialize(d, layouts)
                if "source" in d
                else d,
            )

        for name, meme in memes.items():
            meme.name = name

        return memes
