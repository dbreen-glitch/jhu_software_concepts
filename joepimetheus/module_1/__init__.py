'''Initialize the Flask application and register blueprints.'''
from flask import Flask

# Ensure the running of app imports from correct location
from module_1.pages import bp as pages_bp 


def create_app():
    '''Create and configure the Flask application.'''

    app = Flask(__name__)

    app.register_blueprint(pages_bp)
    return app