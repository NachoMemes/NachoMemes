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
    @abstractmethod
    def refresh_memes(self, guild: Optional[Guild], hard: bool = False) -> str:
        pass

    @abstractmethod
    def get_template_data(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> dict:
        pass

    def get_template(
        self, guild: Optional[Guild], id: str, increment_use: bool = False
    ) -> Template:
        return from_dict(Template, self.get_template_data(guild, id, increment_use), config=da_config)

    @abstractmethod
    def list_memes(self, guild: Union[Guild, str, None] = None, fields: List[str] = None) -> Iterable[dict]:
        """Get all the memes as dictionaries, optionally pass fields to get only those fields in the dicts"""
        pass

    @abstractmethod
    def save_meme(self, guild: Optional[Guild], item: dict) -> str:
        pass

    @abstractmethod
    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        pass

    @abstractmethod
    def save_guild_config(self, guild: GuildConfig) -> None:
        pass


def guild_id(guild: Union[Guild, GuildConfig, str, None]) -> str:
    if isinstance(guild, str):
        return guild
    if isinstance(guild, Guild):
        return str(guild.id)
    return "default"
