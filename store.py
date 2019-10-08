from abc import ABC, abstractmethod
from typing import Callable, Iterable, List

from render import MemeTemplate, TextBox


class TemplateError(Exception):
    pass


class Store(ABC):
    @abstractmethod
    def refresh_memes(self, guild: str, hard: bool = False) -> str:
        pass

    @abstractmethod
    def read_meme(
        self, guild: str, id: str, increment_use: bool = False
    ) -> MemeTemplate:
        pass

    @abstractmethod
    def list_memes(self, guild: str, fields: List[str] = None) -> Iterable[dict]:
        pass

    @abstractmethod
    def guild_config(self, guild: str) -> dict:
        pass
