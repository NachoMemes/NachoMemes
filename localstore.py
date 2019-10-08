from typing import Callable, Iterable, List

from render import MemeTemplate, TextBox
from store import Store


class LocalTemplateStore(Store):
    def __init__(self, default_templates: Callable[[str], Iterable[MemeTemplate]]):
        self.default_templates = default_templates

    def refresh_memes(self, guild: str, hard: bool = False):
        return "Memes were not refreshed since a local store is enabled."

    def read_meme(
        self, guild: str, id: str, increment_use: bool = False
    ) -> MemeTemplate:
        return self.default_templates(guild)[id]

    def list_memes(self, guild: str, fields: List[str] = None) -> Iterable[dict]:
        result = (t.serialize() for t in self.default_templates(guild).values())
        if fields:
            result = ({k: d[k] for k in fields} for d in result)
        return result

    def guild_config(self, guild: str) -> dict:
        pass
