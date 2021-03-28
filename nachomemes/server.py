import io
import json

from flask import Flask, jsonify, request, send_file

from nachomemes import Configuration
from nachomemes.store import Store, update_serialization, TemplateEncoder


def make_server(store: Store) -> Flask:
    app = Flask(__name__)

    @app.route('/')
    def root_path():
        return "NachoMemes REST Endpoint"

    @app.route('/api/<guild_id>/memes')
    def list_memes(guild_id):
        return jsonify(update_serialization(store.list_memes(guild_id)))

    @app.route('/api/<guild_id>/memes/<template_id>')
    def get_template_data(guild_id: str, template_id: str):
        data = store.get_template_data(guild_id, template_id)
        return json.dumps(data, cls=TemplateEncoder)

    @app.route('/api/<guild_id>/memes/<template_id>/render')
    def render(guild_id: str, template_id: str):
        meme = store.get_template(guild_id, template_id)
        text = " ".join(request.args.getlist('text'))
        print(text)
        buffer = io.BytesIO()
        meme.render(text, buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='image/png')

    return app


if __name__ == '__main__':
    config = Configuration()
    app = make_server(config.store)
    app.debug = config.debug
    app.run()
