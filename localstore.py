from typing import Callable, Iterable
from render import MemeTemplate, TextBox

class LocalTemplateStore:
    def __init__(
        self,
        default_templates: Callable[[str], Iterable[MemeTemplate]],
    ):
        self.default_templates = default_templates

    def refresh_memes(self, guild: str, hard: bool = False):
        pass

    def read_meme(self, guild: str, id: str, increment_use: bool = False) -> MemeTemplate:
        return self.default_templates[None](id)

    def list_memes(self, guild: str) -> Iterable[dict]:
        templates = self.default_templates[None]
        dicts = map(lambda t: t.serialize, templates)
        dicts = map(lambda d: {"name": d["name"], "description": d["description"]}, dicts)
        return dicts

    def guild_config(self, guild: str) -> dict:
        pass
