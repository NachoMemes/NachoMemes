from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from sys import maxsize
from typing import IO, Callable, Iterable, List, Optional, Union, Dict, Any, Type, Generator
from types import GeneratorType
from urllib.request import Request, urlopen
import atexit, os, re
from decimal import Decimal
from operator import attrgetter

from discord import Member, Role, Guild
from dacite import Config, from_dict
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

# Dacite serializers
serializers = {
    Request: attrgetter("full_url"),
    float: lambda f: Decimal(str(f)),
    Font: attrgetter("name"),
    Color: attrgetter("name"),
    Justify: attrgetter("name"),
}

# Type coercions for serialization
def update_serialization(value: Any, serializers: Dict[Type, Callable]=serializers):
    if type(value) in serializers:
        return serializers[type(value)](value)
    if dict == type(value):
        return {k: update_serialization(v, serializers) for k, v in value.items()}
    if type(value) in (list, GeneratorType):
        return [update_serialization(v, serializers) for v in value]
    return value

class Store(ABC):
    @abstractmethod
    def refresh_memes(self, guild: Optional[Guild], hard: bool = False) -> str:
        pass

    @abstractmethod
    def get_template_data(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> dict:
        """
        Retrieve template data (serialized template) as a dict from the store.
        """
        pass

    def get_template(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> Template:
        """
        Retrieve a template as a Template object from the store.
        """
        return from_dict(Template, self.get_template_data(guild, id, increment_use), config=da_config)

    @abstractmethod
    def list_memes(self, guild: Union[Guild, str, None]=None, fields: List[str] = None) -> Iterable[dict]:
        """
        List all the serialized templates in the store as dictionaries.
        Optionally, pass fields to get only those fields in the dicts.
        """
        pass

    @abstractmethod
    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        """
        Saves a serialized template as a dict to the store.
        """
        pass

    @abstractmethod
    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        """
        Retrieve the guild configuration as a GuildConfig object from the store.
        Takes a Discord.py Guild object (https://discordpy.readthedocs.io/en/latest/api.html#guild).
        """
        pass

    @abstractmethod
    def save_guild_config(self, guild: GuildConfig):
        pass

def guild_id(guild: Union[Guild,GuildConfig,str,None]) -> str:
    """
    Coerces either a Guild, GuildConfig, or string guild ID into a guild ID string.
    Returns "default" if no valid argument was provided.
    """
    if type(guild) == str:
        return guild
    return str(guild.id) if guild else "default"
