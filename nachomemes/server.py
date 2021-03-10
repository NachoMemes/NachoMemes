import io

from flask import Flask, jsonify, request, send_file

from nachomemes import get_store
from nachomemes.store import Store, update_serialization


def make_server(store: Store) -> Flask:
    app = Flask(__name__)

    @app.route('/api/<guild_id>/memes')
    def list_memes(guild_id):
        return jsonify(update_serialization(store.list_memes(guild_id)))

    @app.route('/api/<guild_id>/memes/<template_id>')
    def get_template_data(guild_id: str, template_id: str):
        return jsonify(update_serialization(store.get_template_data(guild_id, template_id)))

    @app.route('/api/<guild_id>/memes/<template_id>/render')
    def render(guild_id: str, template_id: str):
        meme = store.get_template(guild_id, template_id)
        text = request.args.getlist('text')
        buffer = io.BytesIO()
        meme.render(text, buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='image/png')

    return app


if __name__ == '__main__':
    app = make_server(get_store())
    app.debug = True
    app.run()
