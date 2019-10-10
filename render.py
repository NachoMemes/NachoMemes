# -*- coding: utf-8 -*-

import io
import json
import sys
from decimal import Decimal
from enum import Enum, auto
from itertools import chain, takewhile
from math import cos, pi, sin
from os import PathLike
from pathlib import Path
from typing import IO, Callable, Iterable, Tuple
from urllib.request import Request, urlopen

import PIL
from PIL import Image, ImageDraw, ImageFont


def partition_on(pred, seq):
    i = iter(seq)
    while True:
        try:
            n = next(i)
        except StopIteration:
            return
        yield takewhile(lambda v: not pred(v), chain([n], i))


def _reflow_text(text, count):
    if len(text) == count:
        return text
    elif count == 1:
        return ["\n".join(" ".join(l) for l in partition_on(lambda s: s == "/", text))]
    elif "//" in text:
        result = [
            "\n".join(" ".join(l) for l in partition_on(lambda s: s == "/", b))
            for b in partition_on(lambda s: s == "//", text)
        ]
        assert len(result) == count
        return result
    elif "/" in text:
        result = [" ".join(l) for l in partition_on(lambda s: s == "/", text)]
        assert len(result) == count
        return result


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Justify(Enum):
    LEFT = (lambda w1, w2: 0, )
    CENTER = (lambda w1, w2: (w1 - w2) // 2, )
    RIGHT = (lambda  w1, w2: w1 - w2, )

    def __call__(self, *args, **kwargs):
        return self.value[0](*args, **kwargs)


class Font(Enum):
    IMPACT = Path("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf")
    XKCD = Path("fonts/xkcd-script.ttf")
    COMIC_SANS = Path("/usr/share/fonts/truetype/msttcorefonts/comic.ttf")

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

    def render_rotated(self, img: Image, font_size, color: Color, x, y, angle, string):
        font = self.load(font_size)
        txt = Image.new("RGBA", (800, 400), (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        d.text((0, 0), string, (0, 0, 0, 255), font)
        w = txt.rotate(angle, expand=1)
        img.paste(w, (x, y), w)


class TextBox:
    """ Definition for text that will be placed in a template.

    The left, right, top, and bottom values are expressed as a decimal percentage of the target image
    """

    @staticmethod
    def deserialize(src_dict):
        return TextBox(
            float(src_dict["left"]),
            float(src_dict["right"]),
            float(src_dict["top"]),
            float(src_dict["bottom"]),
            Font[src_dict["face"]],
            src_dict.get("max-font-size", sys.maxsize),
            Justify[src_dict["justify"]],
            Color[src_dict.get("color", "BLACK")],
            Color[src_dict["outline"]] if src_dict.get("outline", None) else None,
            float(src_dict.get("rotation", 0)),
        )

    def serialize(self):
        return {
            "left": Decimal(str(self.left)),
            "right": Decimal(str(self.right)),
            "top": Decimal(str(self.top)),
            "bottom": Decimal(str(self.bottom)),
            "face": self.face.name,
            "justify": self.justify.name,
            "color": self.color.name,
            "outline": self.outline.name if self.outline else None,
            "rotation": Decimal(str(self.rotation)),
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
        rotation,
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
        self.rotation = rotation

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
            for font_size in range(start, 5, -1)
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

    def render(self, img: Image, image_width, image_height, string, font_size):
        lines = string.split("\n")

        # get the size of the bounding box in pixels
        bw, bh = self.box_size(image_width, image_height)

        # find the offset of the first line of text
        top = (bh - font_size * len(lines)) // 2
        for num, line in enumerate(lines):
            font_width = self.face.width(font_size, line)

            # find the start x coordinate of the text within the bounding box 
            # based on the text alignment
            tx = self.justify(bw, font_width)
            ty = top + font_size * num
        
            # translate the text position relative to the position of the text box
            # in the image
            x, y = self.offset(tx, ty, image_width, image_height)
            # render at that position
            if self.rotation:
                self.face.render_rotated(
                    img, font_size, self.color, x, y, self.rotation, line
                )
            elif self.outline:
                self.face.render_outlined(
                    ImageDraw.Draw(img), font_size, self.color, self.outline, x, y, line
                )
            else:
                self.face.render(ImageDraw.Draw(img), font_size, self.color, x, y, line)



    def debug_box(self, img: Image, image_width, image_height):
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            (
                (image_width * self.left, image_height * self.top),
                (image_width * self.right, image_height * self.bottom),
            ),
            outline=(0, 0, 0),
        )


class MemeTemplate:
    """definition for a template
    """

    @staticmethod
    def deserialize(src_dict, layouts=None):
        result = MemeTemplate(
            Request(src_dict["source"]),
            src_dict["layout"],
            [TextBox.deserialize(t) for t in src_dict["textboxes"]]
            if src_dict.get("textboxes", None)
            else layouts[src_dict["layout"]],
            src_dict["description"],
            src_dict["docs"],
            src_dict.get("usage", 0),
        )
        if src_dict.get("name", None):
            result.name = src_dict["name"]
        return result

    def serialize(self, deep=False):
        result = {
            "name": self.name,
            "description": self.description,
            "docs": self.docs,
            "source": self.source.full_url,
            "layout": self.layout,
            "usage": self.usage,
        }
        if deep:
            result["textboxes"] = [t.serialize() for t in self.textboxes]
        return result

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
        self.box_count = len(textboxes)
        self.layout = layout
        self.description = description
        self.docs = docs
        self.usage = usage
        with io.BytesIO() as buffer:
            img = self.read(buffer)
            self.width, self.height = img.size

    def read(self, buffer) -> Image:
        with urlopen(self.source) as s:
            buffer.write(s.read())
            buffer.flush
            buffer.seek(0)
            return Image.open(buffer)

    def render(self, message: Iterable[str], output: IO, show_boxes: bool = False):
        strings = _reflow_text(message, len(self.textboxes))
        texts = list(zip(self.textboxes, strings))
        font_size = min(tb.font_size(self.width, self.height, s) for tb, s in texts)

        with io.BytesIO() as buffer:
            img = self.read(buffer)
            for tb, s in texts:
                tb.render(img, self.width, self.height, s, font_size)
                if show_boxes:
                    tb.debug_box(img, self.width, self.height)

            img.save(output, format="PNG")

    def debug(self, output: IO):
        with io.BytesIO() as buffer:
            img = self.read(buffer)
            for tb in self.textboxes:
                tb.debug_box(img, self.width, self.height)
            img.save(output, format="PNG")


if __name__ == "__main__":
    args = sys.argv[1:]
    show_boxes = False
    if "--show" in args:
        show_boxes = True
        args.remove("--show")
    (filename, template_name, *text) = args
    from localstore import LocalTemplateStore

    store = LocalTemplateStore()
    template = store.read_meme(None, template_name)
    with open(filename, "wb") as f:
        template.render(text, f, show_boxes)
