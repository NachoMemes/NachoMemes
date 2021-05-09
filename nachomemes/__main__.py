import sys
from typing import cast
from io import BufferedIOBase
from nachomemes import Configuration

# Render memes by default when calling:
# python -m nachomemes <output_filename> <template_name> <text>
# Example: python -m nachomemes bruh.png bruh bruh top / bottom
if __name__ == "__main__":
    args = sys.argv[1:]
    show_boxes = False
    if "--show" in args:
        show_boxes = True
        args.remove("--show")
    (filename, template_name, *text) = args

    config = Configuration(["--local"])
    with cast(BufferedIOBase, open(filename, "wb")) as f:
        config.store.get_template(None, template_name).render(" ".join(text), f)