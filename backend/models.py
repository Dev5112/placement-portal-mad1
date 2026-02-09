from flask_sqlalchemy import SQLAlchemy  # type: ignore[import]
from datetime import datetime

db = SQLAlchemy()

# -----------------------------
# USER MODEL (Admin / Company / Student)
# -----------------------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Roles: ADMIN, COMPANY, STUDENT
    role = db.Column(db.String(20), nullable=False)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company_profile = db.relationship(
        "CompanyProfile", backref="user", uselist=False, cascade="all, delete"
    )
    student_profile = db.relationship(
        "StudentProfile", backref="user", uselist=False, cascade="all, delete"
    )

    applications = db.relationship(
        "Application", backref="student", cascade="all, delete", lazy=True
    )


# -----------------------------
# COMPANY PROFILE
# -----------------------------
class CompanyProfile(db.Model):
    __tablename__ = "company_profile"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(150))

    approval_status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING / APPROVED / REJECTED

    is_blacklisted = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    placement_drives = db.relationship(
        "PlacementDrive", backref="company", cascade="all, delete", lazy=True
    )


# -----------------------------
# STUDENT PROFILE
# -----------------------------
class StudentProfile(db.Model):
    __tablename__ = "student_profile"

    id = db.Column(db.Integer, primary_key=True)
    qualification = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String(250))
    resume_path = db.Column(db.String(250))

    is_blacklisted = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# -----------------------------
# PLACEMENT DRIVE / JOB POSTING
# -----------------------------
class PlacementDrive(db.Model):
    __tablename__ = "placement_drive"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    application_deadline = db.Column(db.Date, nullable=False)

    status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING / APPROVED / CLOSED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profile.id"), nullable=False
    )

    applications = db.relationship(
        "Application", backref="placement_drive", cascade="all, delete", lazy=True
    )


# -----------------------------
# APPLICATION (Student ↔ Drive)
# -----------------------------
class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(
        db.String(20), default="APPLIED"
    )  # APPLIED / SHORTLISTED / SELECTED / REJECTED / PLACED

    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)

    # Prevent duplicate applications
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="unique_application"),
    )
