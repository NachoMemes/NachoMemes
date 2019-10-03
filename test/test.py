import sys
import json, os

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from  memegenerator import MemeTemplate,  TextBox

# load layouts
with open("config/layouts.json", "rb") as t:
    layouts = json.load(t, object_hook=lambda d: TextBox.deserialize(d) if "face" in d else d)

# load meme templates
with open("config/templates.json", "rb") as t:
    memes = json.load(t, object_hook=lambda d: MemeTemplate.deserialize(d, layouts) if "source" in d else d)

def _test_drake_meme():
    with open("text2.png", 'wb') as f:
        memes["drake"].render(("Doing something\nuseful with\nyour time","Writing a\nmeme bot\nin Python"), f)

def _test_dump_memes():
    with open("test.json", "w") as t:
        json.dump(memes, t, default=lambda o: o.serialize())

def _test_dump_layouts():
    with open("test/test.json", "w") as t:
        json.dump(layouts, t, indent=2, default=lambda o: o.serialize())

def main():
    _test_drake_meme()
    _test_dump_memes()
    _test_dump_layouts()
    print("All tests run.")

if __name__ == "__main__":
    main()