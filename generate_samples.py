SAMPLES = (("bruh.png", "bruh", '"" / bruh'),)


if __name__ == "__main__":
    import shlex
    from nachomemes import LocalTemplateStore

    store = LocalTemplateStore()
    for filename, name, message in SAMPLES:
        template = store.read_meme(None, name)
        with open(f"sample-memes/{filename}", "wb") as f:
            template.render(shlex.split(message), f)
