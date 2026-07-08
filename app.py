from flask import Flask, render_template
from extensions import db
from config import Config
from tools.site_report.routes import bp as site_report_bp
from tools.construction_assistant.routes import bp as construction_assistant_bp

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]

db.init_app(app)

app.register_blueprint(site_report_bp)
app.register_blueprint(construction_assistant_bp)


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True)
