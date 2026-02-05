from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from extensions import db, login_manager
from models import (
    Admin, Company, Student,
    PlacementDrive, Application
)

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    login_user, logout_user,
    login_required, current_user
)
from werkzeug.utils import secure_filename
import os

# -------------------------------------------------
# App Factory
# -------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"] = "static/uploads/resumes"

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

# -------------------------------------------------
# Flask-Login User Loader
# -------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return (
        Admin.query.get(int(user_id))
        or Company.query.get(int(user_id))
        or Student.query.get(int(user_id))
    )

# -------------------------------------------------
# Authentication Routes
# -------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = None
        if role == "admin":
            user = Admin.query.filter_by(username=email).first()
        elif role == "company":
            user = Company.query.filter_by(
                email=email,
                approved=True,
                blacklisted=False
            ).first()
        elif role == "student":
            user = Student.query.filter_by(
                email=email,
                blacklisted=False
            ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for(f"{role}_dashboard"))

        flash("Invalid credentials or access denied")

    return render_template("auth/login.html")


@app.route("/register/student", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        student = Student(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            skills=request.form["skills"]
        )
        db.session.add(student)
        db.session.commit()
        flash("Student registered successfully")
        return redirect(url_for("login"))

    return render_template("auth/student_register.html")


@app.route("/register/company", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        company = Company(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            hr_contact=request.form["hr_contact"],
            website=request.form["website"]
        )
        db.session.add(company)
        db.session.commit()
        flash("Company registered. Waiting for admin approval.")
        return redirect(url_for("login"))

    return render_template("auth/company_register.html")

# -------------------------------------------------
# Admin Routes
# -------------------------------------------------

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        return redirect(url_for("login"))

    return render_template(
        "admin/dashboard.html",
        students=Student.query.count(),
        companies=Company.query.count(),
        drives=PlacementDrive.query.count(),
        applications=Application.query.count()
    )


@app.route("/admin/companies")
@login_required
def admin_companies():
    if not isinstance(current_user, Admin):
        return redirect(url_for("login"))

    return render_template(
        "admin/companies.html",
        companies=Company.query.all()
    )


@app.route("/admin/company/<int:cid>/approve")
@login_required
def approve_company(cid):
    company = Company.query.get_or_404(cid)
    company.approved = True
    db.session.commit()
    return redirect(url_for("admin_companies"))


@app.route("/admin/company/<int:cid>/reject")
@login_required
def reject_company(cid):
    company = Company.query.get_or_404(cid)
    db.session.delete(company)
    db.session.commit()
    return redirect(url_for("admin_companies"))


@app.route("/admin/students")
@login_required
def admin_students():
    return render_template(
        "admin/students.html",
        students=Student.query.all()
    )


@app.route("/admin/student/<int:sid>/blacklist")
@login_required
def blacklist_student(sid):
    student = Student.query.get_or_404(sid)
    student.blacklisted = True
    db.session.commit()
    return redirect(url_for("admin_students"))


@app.route("/admin/drives")
@login_required
def admin_drives():
    return render_template(
        "admin/drives.html",
        drives=PlacementDrive.query.all()
    )


@app.route("/admin/drive/<int:did>/approve")
@login_required
def approve_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    drive.status = "Approved"
    db.session.commit()
    return redirect(url_for("admin_drives"))


@app.route("/admin/drive/<int:did>/reject")
@login_required
def reject_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    drive.status = "Rejected"
    db.session.commit()
    return redirect(url_for("admin_drives"))

# -------------------------------------------------
# Company Routes
# -------------------------------------------------

def company_access_required():
    return (
        isinstance(current_user, Company)
        and current_user.approved
        and not current_user.blacklisted
    )


@app.route("/company/dashboard")
@login_required
def company_dashboard():
    if not company_access_required():
        return redirect(url_for("login"))

    drives = PlacementDrive.query.filter_by(
        company_id=current_user.id
    ).all()

    return render_template("company/dashboard.html", drives=drives)


@app.route("/company/drive/create", methods=["GET", "POST"])
@login_required
def create_drive():
    if not company_access_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        drive = PlacementDrive(
            job_title=request.form["title"],
            description=request.form["description"],
            eligibility=request.form["eligibility"],
            deadline=request.form["deadline"],
            company_id=current_user.id
        )
        db.session.add(drive)
        db.session.commit()
        return redirect(url_for("company_dashboard"))

    return render_template("company/create_drive.html")


@app.route("/company/drive/<int:did>/applications")
@login_required
def view_applications(did):
    drive = PlacementDrive.query.get_or_404(did)

    if drive.company_id != current_user.id:
        return redirect(url_for("company_dashboard"))

    return render_template(
        "company/applications.html",
        drive=drive,
        applications=Application.query.filter_by(drive_id=did).all()
    )


@app.route("/company/application/<int:aid>/<status>")
@login_required
def update_application_status(aid, status):
    appn = Application.query.get_or_404(aid)
    appn.status = status
    db.session.commit()
    return redirect(request.referrer)

# -------------------------------------------------
# Student Routes ( Milestone-5 )
# -------------------------------------------------

def student_access_required():
    return (
        isinstance(current_user, Student)
        and not current_user.blacklisted
    )


@app.route("/student/dashboard")
@login_required
def student_dashboard():
    if not student_access_required():
        return redirect(url_for("login"))

    return render_template(
        "student/dashboard.html",
        drives=PlacementDrive.query.filter_by(status="Approved").all(),
        applications=Application.query.filter_by(
            student_id=current_user.id
        ).all()
    )


@app.route("/student/apply/<int:did>")
@login_required
def apply_drive(did):
    if not student_access_required():
        return redirect(url_for("login"))

    if not Application.query.filter_by(
        student_id=current_user.id,
        drive_id=did
    ).first():
        db.session.add(Application(
            student_id=current_user.id,
            drive_id=did
        ))
        db.session.commit()

    return redirect(url_for("student_dashboard"))


@app.route("/student/profile", methods=["GET", "POST"])
@login_required
def student_profile():
    if not student_access_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        current_user.skills = request.form["skills"]

        file = request.files.get("resume")
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            current_user.resume = filename

        db.session.commit()
        return redirect(url_for("student_dashboard"))

    return render_template("student/profile.html")

# -------------------------------------------------
# Logout
# -------------------------------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
