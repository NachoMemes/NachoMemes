import sys
from . import get_store

if __name__ == "__main__":
    args = sys.argv[1:]
    show_boxes = False
    if "--show" in args:
        show_boxes = True
        args.remove("--show")
    (filename, template_name, *text) = args

    with open(filename, "wb") as f:
        get_store().get_template(None, template_name).render(text, f)