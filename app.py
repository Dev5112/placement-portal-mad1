from backend import create_app
from backend.models import db, User
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

app = create_app()

print("Placement Portal application started...")

# ✅ DB creation + default admin
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role="ADMIN").first()
    if not admin:
        admin = User(
            full_name="Placement Admin",
            email="admin@iitm.ac.in",
            password=generate_password_hash(
                "admin123",
                method="pbkdf2:sha256"
            ),
            role="ADMIN"
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(port=5002)
