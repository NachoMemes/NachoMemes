import io

from flask import Flask, jsonify, request, send_file

from nachomemes import get_store
from nachomemes.store import Store, update_serialization


def make_server(store: Store) -> Flask:
    app = Flask(__name__)

    @app.route('/api/<guild>/memes')
    def list_memes(guild):
        return jsonify(update_serialization(store.list_memes(guild)))

    @app.route('/api/<guild>/memes/<id>')
    def get_template_data(guild: str, id: str):
        return jsonify(update_serialization(store.get_template_data(guild, id)))

    @app.route('/api/<guild>/memes/<id>/render')
    def render(guild: str, id: str):
        meme = store.get_template(guild, id)
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
    app.debug = True
    app.run()
