
from .guild_config import GuildConfig
from .store import Color, Font, Justify, TextBox, MemeTemplate, Store, da_config, TemplateError, guild_id
from .dynamo_store import DynamoTemplateStore
from .local_store import LocalTemplateStore
from .render import render_template


def get_store(local: bool=True, debug: bool=True) -> Store:
    creds = get_creds(debug) if not local else None
    store = LocalTemplateStore()
    if not local and "access_key" in creds:
        store = DynamoTemplateStore(
            creds["access_key"], creds["secret"], creds["region"], store, debug
        )    
    return store


def get_creds(debug: bool=True) -> dict:
    try:
        creds_file_name = (
            "config/creds.json" if not debug else "config/testing-creds.json"
        )
        with open(os.path.dirname(__file__) + "/../" + creds_file_name, "rb") as f:
            creds = json.load(f)
    except:
        creds = {}
    for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
        if k in os.environ:
            creds[k.lower()] = os.environ[k]
    return creds

if __name__ == "__main__":
    args = sys.argv[1:]
    show_boxes = False
    if "--show" in args:
        show_boxes = True
        args.remove("--show")
    (filename, template_name, *text) = args

    with open(filename, "wb") as f:
        get_store().read_meme(None, template_name).render(text, f)