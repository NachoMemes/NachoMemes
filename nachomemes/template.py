import sys
import atexit
import re
import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import IO, Iterable, List, Optional, Dict
from tempfile import NamedTemporaryFile

from urllib.request import Request, urlopen
from PIL import ImageFont, Image

# Monkeypatch Request to show the url in repr
Request.__repr__ = lambda self: f"Request(<{self.full_url}>)"

# Local file cache for fetched images
LOCAL_IMAGE_CACHE: Dict[str, str] = {}

# Delete the local file cache when an exit is encountered
@atexit.register
def _delete_cache():
    for f in LOCAL_IMAGE_CACHE.values():
        os.remove(f)

class TemplateError(Exception):
    """
    An error with a template.
    """

class Color(Enum):
    """
    Tuple color definition in the format (R, G, B).
    """
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

class Justify(Enum):
    """
    Enum representing horizontal text position.
    Lambda function which calculates left offset from
    the enclosing box.
    """

    LEFT = (lambda w1, w2: 0,)
    CENTER = (lambda w1, w2: (w1 - w2) // 2,)
    RIGHT = (lambda w1, w2: w1 - w2,)

    def __call__(self, *args, **kwargs):
        return self.value[0](*args, **kwargs)

class Font(Enum):
    """
    Enum representing local font files available for loading.
    """
    IMPACT = Path("fonts/impact.ttf")
    XKCD = Path("fonts/xkcd-script.ttf")
    COMIC_SANS = Path("fonts/comic.ttf")

    def load(self, font_size: int) -> ImageFont:
        """
        Load the local font file into a font object.
        """
        return ImageFont.truetype(str(self.value), font_size)

@dataclass
class TextBox:
    """
    Text box to be placed into a template.
    """

    # Offsets from the top left corner as a percentage of the target image
    left: float
    right: float
    top: float
    bottom: float

    # Font for the text
    font: Font

    # Optional maximum font size in pixels
    # Defaults to the system's maximum size
    max_font_size: Optional[int]

    color: Color = Color.BLACK

    outline: Optional[Color] = None

    # Text alignment
    justify: Justify = Justify.CENTER

    # Rotation in degrees
    rotation: Optional[int] = 0

    # if this textbox is sized independently of the other boxes
    ind_size: Optional[bool] = False

def _fetch_image(url: Request) -> IO:
    """
    Fetch an image from a URL and return an IO stream.
    """
    if url.type == 'file':
        return urlopen(url)
    if url.full_url not in LOCAL_IMAGE_CACHE:
        print(f'Loading image {url.full_url} from local cache miss')
        suffix = re.sub(r'[\W]', '', url.full_url.split('.')[-1])[:5]
        with NamedTemporaryFile(suffix='.' + suffix, delete=False) as f:
            with urlopen(url) as u:
                f.write(u.read())
            LOCAL_IMAGE_CACHE[url.full_url] = f.name
        print(f.name)
    return open(LOCAL_IMAGE_CACHE[url.full_url], 'rb')

@dataclass
class Template:
    """
    Template which represents a single meme with text.
    """

    # Name of the template
    name: str

    # URL to load the image
    image_url: Request

    # Where to put the text
    textboxes: List[TextBox]

    # name of the layout
    layout: str

    # A short description
    description: str

    # Documentation for further information
    docs: str

    # times used
    usage: int = 0

    def read_source_image(self, buffer) -> Image:
        """
        Read the source image into an Image object.
        """
        with _fetch_image(self.image_url) as s:
            buffer.write(s.read())
            buffer.seek(0)
            return Image.open(buffer)

    def render(self, message: Iterable[str], output: IO):
        """
        Renders the image into the local filesystem.
        """
        from nachomemes import render_template
        render_template(self, message, output)
