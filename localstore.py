from typing import Callable, Iterable
from render import MemeTemplate, TextBox

class LocalTemplateStore:
    def __init__(
        self,
        default_templates: Callable[[str], Iterable[MemeTemplate]],
    ):
        self.default_templates = default_templates

    def refresh_memes(self, guild: str, hard: bool = False):
        return "Memes were not refreshed since dev mode is enabled."

    def read_meme(self, guild: str, id: str, increment_use: bool = False) -> MemeTemplate:
        return self.default_templates(guild)[id]

    def list_memes(self, guild: str) -> Iterable[dict]:
        return ({"name": t.name, "description": t.description} for t in self.default_templates(guild))

    def guild_config(self, guild: str) -> dict:
        pass
