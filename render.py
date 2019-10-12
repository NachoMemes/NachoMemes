# pylint: skip-file
# # -*- coding: utf-8 -*-

import io
import json
import sys
from decimal import Decimal
from enum import Enum, auto
from itertools import chain, takewhile
from math import cos, pi, sin
from os import PathLike
from pathlib import Path
from typing import IO, Callable, Iterable, Tuple, List
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



class Render:
    def __init__(self, template: MemeTemplate, message: Iterable[str], show_boxes: bool = False):
        self.template = template
        self.message = message
        self.show_boxes = show_boxes
        self.width, self.height = self.template.width, self.template.height


    def box_size(self, tb: TextBox) -> int:
        return (
            int((tb.right - tb.left) * self.width),
            int((tb.bottom - tb.top) * self.height),
        )

    def font_size(self, tb: TextBox, lines: List[str]) -> int:
        width, height = self.box_size(tb)
        start = min(height//len(lines), tb.max_font_size)
        return next(
            font_size
            for font_size in range(start, 5, -1)
            if all(tb.face.width(font_size, s) < width for s in lines)
        )

    def render(self, output: IO):
        # combine the strings into the required number of textboxes
        strings = _reflow_text(self.message, len(self.template.textboxes))

        # zip the strings up with the corrosponding textbox
        texts = list(zip(self.template.textboxes, [s.split('\n') for s in strings]))

        # Find the smallest required font size for all non-independent textboxes
        base_size = min(self.font_size(tb, s) for tb, s in texts if not tb.ind_size)

        with io.BytesIO() as buffer:
            self.img = self.template.read(buffer)
            for tb, s in texts:
                # if tb.concat:
                #     continue
                self.render_box(tb, s, base_size)
                if show_boxes:
                    tb.debug_box(img, width, height)

            self.img.save(output, format="PNG")


    def render_box(self, tb: TextBox, lines: List[str], base_size: int):

        # if this is independently sized, calculate the size
        fsize = base_size if tb.ind_size else self.font_size(tb, lines)

        # get the size of the bounding box in pixels
        bw, bh = self.box_size(tb)

        # find the offset of the first line of text
        top = (bh - fsize * len(lines)) // 2
        for num, line in enumerate(lines):
            font_width = tb.face.width(fsize, line)

            # find the start x coordinate of the text within the bounding box 
            # based on the text alignment
            tx = tb.justify(bw, font_width)
            ty = top + fsize * num
        
            # translate the text position relative to the position of the text box
            # in the image
            x, y = self.offset(tb, tx, ty)
            # render at that position
            if tb.rotation:
                tb.face.render_rotated(
                    img, fsize, tb.color, x, y, tb.rotation, line
                )
            elif tb.outline:
                tb.face.render_outlined(
                    ImageDraw.Draw(img), fsize, tb.color, tb.outline, x, y, line
                )
            else:
                tb.face.render(ImageDraw.Draw(self.img), fsize, tb.color, x, y, line)

    def offset(self, tb: TextBox, x: int, y: int) -> Tuple[int, int]:
        return int(tb.left * self.width) + x, int(tb.top * self.height) + y

    def width(self, font_size: int, string: str) -> int:
        return self.load(font_size).getsize(string)[0]

    def render_outlined(
        self, tb:TextBox, font_size: int, color: Color, outline: Color, x, y, string
    ):
        font = self.tb.font.load(font_size)
        offset = font_size / 15
        for angle in range(0, 360, 30):
            r = angle / 360 * 2 * pi
            pos = (x + (cos(r) * offset)k, y + (sin(r) * offset))
            draw.text(pos, string, outline.value, font)
        self.render(draw, font_size, color, x, y, string)

    def render_plain(self, draw, font_size, color: Color, x, y, string):
        font = self.load(font_size)
        draw.text((x, y), string, color.value, font)

    def render_rotated(self, img: Image, font_size, color: Color, x, y, angle, string):
        font = self.load(font_size)
        txt = Image.new("RGBA", (800, 400), (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        d.text((0, 0), string, (0, 0, 0, 255), font)
        w = txt.rotate(angle, expand=1)
        img.paste(w, (x, y), w)


    def debug_box(self, tb: TextBox):
        draw = ImageDraw.Draw(self.img)
        draw.rectangle(
            (
                (self.image_width * tb.left, self.image_height * tb.top),
                (self.image_width * tb.right, self.image_height * tb.bottom),
            ),
            outline=(0, 0, 0),
        )


if __name__ == "__main__":
    args = sys.argv[1:]
    show_boxes = False
    if "--show" in args:
        show_boxes = True
        args.remove("--show")
    (filename, template_name, *text) = args
    from localstore import LocalTemplateStore

    store = LocalTemplateStore()
    render = Render(store.read_meme(None, template_name), text, show_boxes)
    with open(filename, "wb") as f:
        render.render(f)
