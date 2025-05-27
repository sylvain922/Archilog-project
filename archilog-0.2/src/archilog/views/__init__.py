from flask import Flask
from archilog.views.gui import web_ui

def create_app():
    app = Flask(__name__)

    app.config.from_prefixed_env(prefix="ARCHILOG_FLASK")
    app.register_blueprint(web_ui, url_prefix="/")

    return app
