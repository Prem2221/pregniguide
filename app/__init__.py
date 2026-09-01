from flask import Flask, render_template

from config.settings import settings


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/static")
    app.secret_key = settings.flask_secret_key

    from app.routes import bp
    app.register_blueprint(bp)

    @app.route("/")
    def home():
        return render_template("index.html")

    return app