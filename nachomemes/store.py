from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from sys import maxsize
from typing import IO, Callable, Iterable, List, Optional, Union, Dict
from urllib.request import Request, urlopen
import atexit, os, re

from discord import Member, Role, Guild
from dacite import Config
from PIL import Image, ImageFont

from .guild_config import GuildConfig
from .template import Template, Font, Color, Justify

# additional deserializers for dacite
da_config = Config(
    {
        Font: Font.__getitem__,
        Color: Color.__getitem__,
        Justify: Justify.__getitem__,
        Request: Request,
        float: float,
        int: int,
    }
)

class Store(ABC):
    @abstractmethod
    def refresh_memes(self, guild: Optional[Guild], hard: bool = False) -> str:
        pass

    @abstractmethod
    def read_meme(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> Template:
        pass

    @abstractmethod
    def list_memes(self, guild: Optional[Guild], fields: List[str] = None) -> Iterable[dict]:
        "Get all the memes as dictionaries, optionally pass fields to get only those fields in the dicts"
        pass

    @abstractmethod
    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        pass

    @abstractmethod
    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        pass

    @abstractmethod
    def save_guild_config(self, guild: GuildConfig):
        pass

def guild_id(guild: Union[Guild,GuildConfig,None]) -> str:
    return str(guild.id) if guild else "default"
