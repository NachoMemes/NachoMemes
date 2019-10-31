from flask import Flask, url_for, jsonify, request, make_response, send_file
import io

from . import get_store
from .store import Store, update_serialization


def make_server(store: Store) -> Flask:
    app = Flask(__name__)

    @app.route('/api/<guild>/memes')
    def list_memes(guild):
        return jsonify(update_serialization(store.list_memes(guild)))

    @app.route('/api/<guild>/memes/<id>')
    def get_meme(guild: str, id: str):
        return jsonify(update_serialization(store.get_meme(guild, id)))

    @app.route('/api/<guild>/memes/<id>/render')
    def render(guild: str, id: str):
        meme = store.meme(guild, id)
        text = request.args.getlist('text')
        buffer = io.BytesIO()
        meme.render(text, buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='image/png')

    return app

if __name__ == '__main__':
    store = get_store()
    app = make_server(store)
    app.debug=True
    app.run()