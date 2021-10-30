"""server serves the serving"""
import io
from decimal import Decimal
from urllib.parse import unquote
import re, os

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask.json import JSONEncoder

from nachomemes import Configuration, Store

FILE_URL = re.compile(r'file\:source_images\/([\w]+\.[\w]+)')
IMAGE_DIR = os.path.join(os.getcwd(), 'source_images')

class TemplateEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(TemplateEncoder, self).default(obj)

def make_server(store: Store, webroot: str) -> Flask:
    app = Flask(__name__, static_folder=webroot, static_url_path="/templates")
    app.json_encoder = TemplateEncoder

    @app.route("/")
    def root_path():
        return "NachoMemes REST Endpoint"

    @app.route("/api/<guild_id>/memes")
    def list_memes(guild_id):
        return jsonify(store.list_memes(guild_id, ("name", "description", "preview_url")))

    @app.route("/api/<guild_id>/memes-name")
    def list_of_meme_names(guild_id):
        data = store.list_memes(guild_id)
        list_names = []
        for entry in data:
            list_names.append(entry['name'])
        return jsonify()

    @app.route("/api/<guild_id>/memes/<template_id>")
    def get_template_data(guild_id: str, template_id: str):
        data = store.get_template_data(guild_id, template_id)
        return jsonify(data)

    @app.route("/api/<guild_id>/memes/<template_id>/render")
    def render(guild_id: str, template_id: str):
        meme = store.get_template(guild_id, template_id)
        text = "\n".join(request.args.getlist("text"))
        print(text)
        buffer = io.BytesIO()
        meme.render(text, buffer)
        buffer.seek(0)
        return send_file(buffer, mimetype="image/png")  # type: ignore

    @app.route("/api/file/<path:file_url>")
    def serve_image(file_url: str):
        match = FILE_URL.match(unquote(file_url))
        if match:
            return send_from_directory(directory=IMAGE_DIR, path=match.group(1))

    @app.route('/api/<guild_id>/memes/<template_id>/render')
    def baseimage(guild_id: str, template_id: str):
        meme = store.get_template(guild_id, template_id)
        text = " ".join(request.args.getlist('text'))
        print(text)
        buffer = io.BytesIO()
        meme.render(text, buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='image/png')

    @app.route('/api/<guild_id>/save-template/<template_id>', methods=['GET', 'POST'])
    def save_template(guild_id: str, template_id: str):
        print("Updated: " + template_id + " in guild: " + guild_id)
        return store.save_meme(guild_id, request.json)

    return app


if __name__ == "__main__":
    config = Configuration()
    server = make_server(config.store, config.webroot)
    server.debug = config.debug
    server.run()
