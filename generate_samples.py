SAMPLES = (("bruh.png", "bruh", '"" / bruh'),)


if __name__ == "__main__":
    import shlex
    from nachomemes.local_store import LocalTemplateStore

    store = LocalTemplateStore()
    for filename, name, message in SAMPLES:
        template = store.read_meme(None, "bruh")
        with open(f"../sample-memes/{filename}", "wb") as f:
            template.render(shlex.split(message), f)
