from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Union,  Type, cast
from types import GeneratorType
from urllib.request import Request
import atexit, os, re
import json
from decimal import Decimal
from operator import attrgetter
from types import GeneratorType, MappingProxyType
from urllib.request import Request
from fuzzywuzzy import process
from io import BytesIO

import PIL

from dacite import Config, from_dict
from discord import Guild

from nachomemes.uploader import Uploader
from nachomemes.guild_config import GuildConfig
from nachomemes.template import Color, Font, Justify, Template, TemplateError, TextBox

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
    if isinstance(value, TextBox):
        return update_serialization(value.__dict__)
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

    uploader: Uploader

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
    def list_memes(self, guild_id: str, is_deleted: Optional[bool], fields: Optional[Iterable[str]] = None) -> Iterable[dict]:
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

        
    def best_match(self, guild_id: str, name: str = None, increment_use: bool = False
    ) -> Template:
        """Matches input fuzzily against proper names."""
        if name is None:
            raise TemplateError(f"No template name provided")
        fuzzed = process.extractOne(name, self.list_memes(guild_id, ("name",)))
        if fuzzed[1] < 50:
            raise TemplateError(f"No template matching '{name}'")
        return self.get_template(guild_id, fuzzed[0]["name"], increment_use)

    async def best_match_with_preview(
        self, guild_id: str, template_id: str, increment_use: bool = False
    ) -> Template:
        """
        Retrieve a template as a Template object from the store.
        """
        template = self.best_match(guild_id, template_id, increment_use)
        if not template.preview_url:
            if self.uploader:
                with BytesIO() as input:
                    img = template.read_source_image(input)
                    img.thumbnail((256,256), PIL.Image.BICUBIC)
                    with BytesIO() as output:
                        img.save(output, format="PNG")
                        output.flush()
                        output.seek(0)
                        template.preview_url = Request(await self.uploader.upload(output, template.name + '.' + template.image_url.full_url.split('.')[-1]))
                self.save_meme(guild_id, update_serialization(template.__dict__))
        return template

    def close_matches(self, guild_id: str, name: str, is_deleted: Optional[bool], fields: Optional[Iterable[str]] = None) -> List[Dict]:
        """Fuzzy match multiple templates."""
        return [
            match[0]
            for match in process.extract(name, self.list_memes(guild_id, is_deleted, fields))
            if  match[1] > 40
        ]


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
