from flask import Flask

import pages

def create_app():
    app = Flask(__name__)

    app.register_blueprint(pages.bp)
    return app

if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080)
