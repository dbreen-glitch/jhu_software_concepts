from flask import Flask

from module_1.pages import bp as pages_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(pages_bp)
    return app