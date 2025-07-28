from flask import Flask
from flask_cors import CORS

from .database import init_db
from .routes import accounts_bp

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

  
    app.register_blueprint(accounts_bp)

    init_db()

    return app