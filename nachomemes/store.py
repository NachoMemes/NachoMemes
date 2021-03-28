from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Union,  Type, Generator, cast
from types import GeneratorType
from urllib.request import Request
import atexit, os, re
import json
from decimal import Decimal
from operator import attrgetter
from types import GeneratorType, MappingProxyType
from urllib.request import Request
from fuzzywuzzy import process

from dacite import Config, from_dict
from discord import Guild

from nachomemes.guild_config import GuildConfig
from nachomemes.template import Color, Font, Justify, Template, TemplateError

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
serializers = cast(dict, MappingProxyType({
    Request: attrgetter("full_url"),
    float: lambda f: Decimal(str(f)),
    Font: attrgetter("name"),
    Color: attrgetter("name"),
    Justify: attrgetter("name"),
}))


def update_serialization(value: Any, _serializers: Dict[Type, Callable] = serializers):
    """helper function to recursivly modify the format of data prior to serialization"""
    if type(value) in _serializers:
        return _serializers[type(value)](value)
    if dict == type(value):
        return {k: update_serialization(v, _serializers) for k, v in value.items()}
    if type(value) in (list, GeneratorType):
        return [update_serialization(v, _serializers) for v in value]
    return value

class TemplateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(TemplateEncoder, self).default(obj)

class Store(ABC):
    """
    Abstract base class for implementing data stores for template and guild data.
    """
    @abstractmethod
    def refresh_memes(self, guild_id: str, hard: bool = False) -> str:
        pass

    @abstractmethod
    def get_template_data(
        self, guild_id: str, template_id: str, increment_use: bool = False
    ) -> dict:
        """
        Retrieve template data (serialized template) as a dict from the store.
        """
        

    def get_template(
        self, guild_id: Optional[str], template_id: str, increment_use: bool = False
    ) -> Template:
        """
        Retrieve a template as a Template object from the store.
        """
        return from_dict(Template, self.get_template_data(
            guild_id if guild_id is not None else "default", 
            template_id, increment_use), config=da_config)

    @abstractmethod
    def list_memes(self, guild_id: str, fields: Optional[Iterable[str]] = None) -> Iterable[dict]:
        """
        List all the serialized templates in the store as dictionaries.
        Optionally, pass fields to get only those fields in the dicts.
        """

    @abstractmethod
    def save_meme(self, guild_id: str, item: dict) -> str:
        """
        Saves a serialized template as a dict to the store.
        """

    @abstractmethod
    def guild_config(self, guild: Optional[Guild]) -> GuildConfig:
        """
        Retrieve the guild configuration as a GuildConfig object from the store.
        """

    @abstractmethod
    def save_guild_config(self, guild: GuildConfig) -> None:
        """serialize and persist the guild configuration information in the store"""
        
    def best_match(self, guild_id: str, name: str, increment_use: bool = False
    ) -> Template:
        """Matches input fuzzily against proper names."""
        fuzzed = process.extractOne(name, self.list_memes(guild_id, ("name",)))
        if fuzzed[1] < 25:
            raise TemplateError(f"could not load a template matching {name}")
        return self.get_template(guild_id, fuzzed[0]["name"], increment_use)


    # def _find_close_matches(name: str, guild: GuildConfig) -> list:
    #     """Chooses top matches against input."""
    #     return [
    #         name[0]["name"]
    #         for name in process.extract(name, STORE.list_memes(guild.guild_id, ("name",)))
    #         if name[1] > 40
    #     ]



    def close_matches(self, guild_id: str, name: str, fields: Optional[Iterable[str]] = None) -> List[Dict]:
        """Fuzzy match multiple templates."""
        return [
            match[0]
            for match in process.extract(name, self.list_memes(guild_id, fields))
            if  match[1] > 40
        ]


    # async def single_fuzzed_template(ctx: Context, template: str, guild: GuildConfig):
    #     """Fuzzy match a single template"""
    #     fmeme = _match_template_name(template, guild)
    #     _meme = STORE.get_template(guild.guild_id, fmeme)
    #     await ctx.send(
    #         textwrap.dedent(
    #             f"""\
    #         Name: {_meme.name}
    #         Description: *{_meme.description}*
    #         Times used: {_meme.usage}
    #         Expects {len(_meme.textboxes)} strings
    #         Read more: {_meme.docs}"""
    #         )
    #     )

def get_guild_id(guild: Union[Guild,GuildConfig,str,None]) -> str:
    """
    Coerces either a Guild, GuildConfig, or string guild ID into a guild ID string.
    Returns "default" if no valid argument was provided.
    """
    if isinstance(guild, str):
        return guild
    if isinstance(guild, Guild):
        return str(guild.id)
    if isinstance(guild, GuildConfig):
        return str(guild.guild_id)
    return "default"
