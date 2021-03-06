from abc import ABC, abstractmethod
from decimal import Decimal
from operator import attrgetter
from types import GeneratorType, MappingProxyType
from typing import (Any, Callable, Dict, Iterable, List,
                    Optional, Type, Union)
from urllib.request import Request

from dacite import Config, from_dict
from discord import Guild

from nachomemes.guild_config import GuildConfig
from nachomemes.template import Color, Font, Justify, Template

# additional deserializers for dacite
da_config = Config({
    Font: Font.__getitem__,
    Color: Color.__getitem__,
    Justify: Justify.__getitem__,
    Request: Request,
    float: float,
    int: int,
})

# additional serializers for dacite
serializers: Dict[Type, Callable] = MappingProxyType({
    Request: attrgetter("full_url"),
    float: lambda f: Decimal(str(f)),
    Font: attrgetter("name"),
    Color: attrgetter("name"),
    Justify: attrgetter("name"),
})


def update_serialization(value: Any, _serializers: Dict[Type, Callable] = serializers):
    """helper function to recursivly modify the format of data prior to serialization"""
    if type(value) in _serializers:
        return _serializers[type(value)](value)
    if dict == type(value):
        return {k: update_serialization(v, _serializers) for k, v in value.items()}
    if type(value) in (list, GeneratorType):
        return [update_serialization(v, _serializers) for v in value]
    return value


class Store(ABC):
    """
    Abstract base class for implementing data stores for template and guild data.
    """
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
    def save_guild_config(self, guild: GuildConfig) -> None:
        pass

def guild_id(guild: Union[Guild,GuildConfig,str,None]) -> str:
    """
    Coerces either a Guild, GuildConfig, or string guild ID into a guild ID string.
    Returns "default" if no valid argument was provided.
    """
    if type(guild) == str:
        return guild
    if isinstance(guild, Guild):
        return str(guild.id)
    return "default"
