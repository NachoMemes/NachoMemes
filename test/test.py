import json
import os
import sys

from bot import _reflow_text
from memegenerator import MemeTemplate, TextBox

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)


# load layouts
with open("config/layouts.json", "rb") as t:
    layouts = json.load(t, object_hook=lambda d: TextBox.deserialize(d) if "face" in d else d)

# load meme templates
with open("config/templates.json", "rb") as t:
    memes = json.load(t, object_hook=lambda d: MemeTemplate.deserialize(d, layouts) if "source" in d else d)

def _test_meme():
    # with open("text3.png", 'wb') as f:
    #     memes["millionaire1"].render(("What is the best language to write a bot?","Python", "Scala", "Russian", "Fuck you I'm Joe"), f)
    # with open("text4.png", 'wb') as f:
    #     memes["millionaire1"].render(("Did sam use his first paycheck to get on the tesla wait-list??","Of course", "No doubt", "Elon is God", "TESLA I LUV U"), f)
    # with open("text5.png", 'wb') as f:
    #     memes["pikachu"].render(("Me: Do you have any memebot requests\n\nJoe: I want suprised pikachu\n\nMe:",), f)
    # with open("text6.png", 'wb') as f:
    #     memes["big-brain"].render(("I'm writing a bot","It's big-brain time"), f)
    # with open("text6.png", 'wb') as f:
    #     memes["change-my-mind"].render(("This is the greatest bot\nin the history of mankind",), f)
    # with open("text7.png", 'wb') as f:
    #     memes["successkid"].render(("Can you feel the BDE","radiating off my body?"), f)
    with open("test/text1.png", 'wb') as f:
        memes["boardroom"].render(_reflow_text("boardroom How should we write a bot? / Python / Node / Scala!".split(), 4), f)


def _test_dump_memes():
    with open("test.json", "w") as t:
        json.dump(memes, t, indent=2, default=lambda o: o.serialize())

def _test_dump_layouts():
    with open("test/test.json", "w") as t:
        json.dump(layouts, t, indent=2, default=lambda o: o.serialize())

def main():
    _test_meme()
    _test_dump_memes()
    _test_dump_layouts()
    print("All tests run.")

if __name__ == "__main__":
    main()


# with open("test/text1.png", 'wb') as f:
#     memes['boardroom'].debug(f)
