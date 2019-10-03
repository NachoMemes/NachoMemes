from urllib.request import Request, urlopen

from  memegenerator import MemeTemplate,  TextBox

import json

# url = Request('file:templates/aliens.jpg')

# t = MemeTemplate(url, standard_layout)

# with open("text.png", 'wb') as f:
#     t.render(("ALL CAPS", "SHOULD FIT"), f)


# load layouts
with open("config/layouts.json", "rb") as t:
    layouts = json.load(t, object_hook=lambda d: TextBox.deserialize(d) if "face" in d else d)

# load meme templates
with open("config/templates.json", "rb") as t:
    memes = json.load(t, object_hook=lambda d: MemeTemplate.deserialize(d, layouts) if "source" in d else d)

with open("text2.png", 'wb') as f:
     memes["drake"].render(("Doing something\nuseful with\nyour time","Writing a\nmeme bot\nin Python"), f)

