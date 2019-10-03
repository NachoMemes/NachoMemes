# -*- coding: utf-8 -*-

import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

import sys
import json
import io

from pathlib import Path
from os import PathLike
from math import sin, cos, pi
from enum import Enum, auto
from typing import Tuple, Callable, Iterable, IO
from urllib.request import Request, urlopen

DEBUG = True


def dprint(s):
    if DEBUG:
        print(s)


def dprint(a, b):
    if DEBUG:
        print(a, b)


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Justify(Enum):
    LEFT = (lambda w1, w2: 0,)
    CENTER = (lambda w1, w2: (w1 - w2) // 2,)
    RIGHT = (lambda w1, w2: w1 - w2,)

    def __init__(self, formula: Callable[[int, int], int]):
        self.formula = formula

    def calculate(
        self, width: int, height: int, text_width: int, text_height: int
    ) -> Tuple[int, int]:
        return self.formula(width, text_width), (height - text_height) // 2


class Font(Enum):
    IMPACT = Path("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf")

    def load(self, font_size: int) -> ImageFont:
        return ImageFont.truetype(str(self.value), font_size)

    def width(self, font_size: int, string: str) -> int:
        return self.load(font_size).getsize(string)[0]

    def render_outlined(
        self, draw: ImageDraw, font_size, color: Color, outline: Color, x, y, string
    ):
        font = self.load(font_size)
        offset = font_size / 15
        for angle in range(0, 360, 30):
            r = angle / 360 * 2 * pi
            pos = (x + (cos(r) * offset), y + (sin(r) * offset))
            draw.text(pos, string, outline.value, font)
        self.render(draw, font_size, color, x, y, string)

    def render(self, draw, font_size, color: Color, x, y, string):
        font = self.load(font_size)
        draw.text((x, y), string, color.value, font)


class TextBox:
    """ Definition for text that will be placed in a template.

    The left, right, top, and bottom values are expressed as a decimal percentage of the target image
    """

    @staticmethod
    def deserialize(src_dict):
        return TextBox(
            src_dict["left"],
            src_dict["right"],
            src_dict["top"],
            src_dict["bottom"],
            Font[src_dict["face"]],
            src_dict.get("max-font-size", sys.maxsize),
            Justify[src_dict["justify"]],
            Color[src_dict.get("color", "BLACK")],
            Color[src_dict["outline"]] if src_dict.get("outline", None) else None,
        )

    def serialize(self):
        return {
            "left": self.left,
            "right": self.right,
            "top": self.top,
            "bottom": self.bottom,
            "face": self.face.name,
            "justify": self.justify.name,
            "color": self.color.name,
            "outline": self.outline.name if self.outline else None,
        }

    def __init__(
        self,
        left: float,
        right: float,
        top: float,
        bottom: float,
        face: Font,
        max_font_size: int,
        justify: Justify,
        color: Color,
        outline: Color,
    ):
        assert all(0 < v < 1 for v in (left, right, top, bottom))
        assert left < right and top < bottom

        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.face = face
        self.max_font_size = max_font_size
        self.justify = justify
        self.color = color
        self.outline = outline

    def font_size(self, image_width: int, image_height: int, string: str) -> int:
        if "\n" in string:
            strings = string.split("\n")
            return min(
                self.font_size(image_width, image_height // len(strings), s)
                for s in strings
            )
        width, height = self.box_size(image_width, image_height)
        start = min(height, self.max_font_size)
        return next(
            font_size
            for font_size in range(start, 10, -1)
            if self.face.width(font_size, string) < width
        )

    def box_size(self, image_width: int, image_height: int) -> int:
        return (
            int((self.right - self.left) * image_width),
            int((self.bottom - self.top) * image_height),
        )

    def offset(
        self, x: int, y: int, image_width: int, image_height: int
    ) -> Tuple[int, int]:
        return int(self.left * image_width) + x, int(self.top * image_height) + y

    def render(self, draw: ImageDraw, image_width, image_height, string, font_size):
        lines = string.count("\n") + 1
        # calculate the width of the text in pixels.
        font_width = self.face.width(font_size, string)
        # get the size of the bounding box in pixels
        bw, bh = self.box_size(image_width, image_height)
        # find the start coordinates of the text within the bounding box based
        # on the text alignment
        tx, ty = self.justify.calculate(bw, bh, font_width, font_size * lines)
        # translate the text position relative to the position of the text box
        # in the image
        x, y = self.offset(tx, ty, image_width, image_height)
        # render at that position
        if self.outline:
            self.face.render_outlined(
                draw, font_size, self.color, self.outline, x, y, string
            )
        else:
            self.face.render(draw, font_size, self.color, x, y, string)


class MemeTemplate:
    """definition for a template
    """

    @staticmethod
    def deserialize(src_dict, layouts):
        return MemeTemplate(
            Request(src_dict["source"]),
            src_dict["layout"],
            layouts[src_dict["layout"]],
            src_dict["description"],
            src_dict["docs"],
            src_dict.get("usage", 0),
        )

    def serialize(self):
        return {
            "description": self.description,
            "docs": self.docs,
            "source": self.source.full_url,
            "layout": self.layout,
            "usage": self.usage,
        }

    def __init__(
        self,
        source: Request,
        layout: str,
        textboxes: Iterable[TextBox],
        description: str,
        docs: str,
        usage: int,
    ):
        self.source = source
        self.textboxes = textboxes
        self.layout = layout
        self.description = description
        self.docs = docs
        self.usage = usage
        self.box_count = len(textboxes)
        with io.BytesIO() as buffer:
            img = self.read(buffer)
            self.width, self.height = img.size

    def read(self, buffer) -> Image:
        with urlopen(self.source) as s:
            buffer.write(s.read())
            buffer.flush
            buffer.seek(0)
            return Image.open(buffer)

    def render(self, strings: Iterable[str], output: IO):
        assert len(strings) == len(self.textboxes)
        texts = list(zip(self.textboxes, strings))
        font_size = min(tb.font_size(self.width, self.height, s) for tb, s in texts)

        with io.BytesIO() as buffer:
            img = self.read(buffer)
            draw = ImageDraw.Draw(img)
            for tb, s in texts:
                tb.render(draw, self.width, self.height, s, font_size)

            img.save(output, format="PNG")


# # Load layout data.
# with open("config/layouts.json", "rb") as t:
#     layouts = json.load(t)

