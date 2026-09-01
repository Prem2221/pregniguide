from flask import Flask

from config.settings import settings


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/static")
    app.secret_key = settings.flask_secret_key

    from app.routes import bp
    app.register_blueprint(bp)

    @app.route("/")
    def home():
        return "Pregni Guide API is running. Frontend comes in a later step."

    return app