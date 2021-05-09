import io
import os
import shlex
import sys
import unittest
import zlib
import math
from tempfile import NamedTemporaryFile
from PIL import Image, ImageChops, ImageOps


# currentdir = os.path.dirname(os.path.realpath(__file__))
# parentdir = os.path.dirname(currentdir)
# srcdir = os.path.join(parentdir, "nachomemes")
# sys.path.append(srcdir)

from generate_samples import SAMPLES
from nachomemes import LocalTemplateStore

MAX_ERROR = 0.12
def rmsdiff(d):
    h = ImageOps.grayscale(d).histogram()
    s = sum((count*((value/256)**2) for value, count in enumerate(h)))
    return math.sqrt(s / (float(d.size[0]) * d.size[1]))

def make_diff(expected_filename, template, message):
    with Image.open(f"sample-memes/{expected_filename}") as expected:
        with io.BytesIO() as buffer:
            template.render(message, buffer)
            buffer.flush()
            buffer.seek(0)
            actual = Image.open(buffer)
            return ImageChops.difference(expected, actual)


class TestRender(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRender, self).__init__(*args, **kwargs)
        self.store = LocalTemplateStore()
        self.has_errors = False

    def test_simple(self):
        for filename, name, message in SAMPLES:
            try:
                template = self.store.get_template(None, name)
                diff = make_diff(filename, template, message)
                value = rmsdiff(diff)
                self.assertTrue(value < MAX_ERROR)
            except AssertionError:
                if not self.has_errors:
                    self.has_errors = True
                    with NamedTemporaryFile(suffix=".png", delete=False) as f:
                        diff.save(f, format="PNG")
                        print(f"histogram difference {value} > {MAX_ERROR}; wrote  image diff to {f.name}", file=sys.stderr)
                raise


if __name__ == "__main__":
    unittest.main()
