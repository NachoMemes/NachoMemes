import io
import os
import sys
import unittest
import zlib
import shlex
from tempfile import NamedTemporaryFile

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from localstore import LocalTemplateStore
from generate_samples import SAMPLES

class TestRender(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRender, self).__init__(*args, **kwargs)
        self.store = LocalTemplateStore()
        self.has_errors = False

    def test_simple(self):
        for filename, name, message in SAMPLES:
            template = self.store.read_meme(None, name)
            with open(f'samples/{filename}', 'rb') as f:
                expected = zlib.adler32(f.read())
            with io.BytesIO() as buffer:
                template.render(shlex.split(message), buffer)
                buffer.flush()
                buffer.seek(0)
                actual = zlib.adler32(buffer.read())
            try:
                self.assertEqual(expected, actual)
            except AssertionError:
                if not self.has_errors:
                    self.has_errors = True
                    buffer.seek(0)
                    with NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(buffer.read())
                        print(f"wrote failed image to {f.name}", file=sys.stderr)
                raise


if __name__ == "__main__":
    unittest.main()
