import io
import os
import sys
import unittest
import zlib
from tempfile import NamedTemporaryFile

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from render import default_templates


class TestRender(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRender, self).__init__(*args, **kwargs)
        self.templates = default_templates(None)
        self.has_errors = False

    def test_simple(self):
        template = self.templates["bruh"]
        with io.BytesIO() as buffer:
            template.render(("", "bruh"), buffer)
            buffer.flush()
            buffer.seek(0)
            try:
                self.assertEqual(4024085169, zlib.adler32(buffer.read()))
            except AssertionError:
                if not self.has_errors:
                    self.has_errors = True
                    buffer.seek(0)
                    with NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(buffer.read())
                        print(f"wrote image to {f.name}", file=sys.stderr)
                raise


if __name__ == "__main__":
    unittest.main()
