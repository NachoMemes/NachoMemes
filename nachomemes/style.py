from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import sys

from PIL import ImageFont

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
    face: Font

    # Optional maximum font size in pixels
    # Defaults to the system's maximum size
    max_font_size: Optional[int] = sys.maxsize

    color: Color = Color.BLACK

    outline: Optional[Color] = None

    # Text alignment
    justify: Justify = Justify.CENTER

    # Rotation in degrees
    rotation: Optional[int] = 0

    # if this textbox is sized independently of the other boxes
    ind_size: Optional[bool] = False
