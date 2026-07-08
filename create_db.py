from app import app, db
import models  # noqa: F401


with app.app_context():
    db.create_all()
    print("Database tables created.")