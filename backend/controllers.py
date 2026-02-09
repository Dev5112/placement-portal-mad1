from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from .models import db, User, CompanyProfile, StudentProfile, PlacementDrive, Application

bp = Blueprint("main", __name__)

# =========================================================
# HOME
# =========================================================
@bp.route("/")
def home():
    return render_template("index.html")


# =========================================================
# AUTHENTICATION
# =========================================================
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, is_active=True).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role
            session["name"] = user.full_name

            if user.role == "ADMIN":
                return redirect(url_for("main.admin_dashboard"))
            elif user.role == "COMPANY":
                return redirect(url_for("main.company_dashboard"))
            else:
                return redirect(url_for("main.student_dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


# =========================================================
# STUDENT REGISTRATION
# =========================================================
@bp.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already exists", "warning")
            return redirect(url_for("main.student_register"))

        user = User(
            full_name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(
                request.form["password"],
                method="pbkdf2:sha256"
            ),
            role="STUDENT"
        )

        db.session.add(user)
        db.session.commit()

        profile = StudentProfile(
            qualification=request.form["qualification"],
            skills=request.form["skills"],
            user_id=user.id
        )

        db.session.add(profile)
        db.session.commit()

        return redirect(url_for("main.login"))

    return render_template("student_register.html")


# =========================================================
# COMPANY REGISTRATION
# =========================================================
@bp.route("/company/register", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already exists", "warning")
            return redirect(url_for("main.company_register"))

        user = User(
            full_name=request.form["hr_name"],
            email=request.form["email"],
            password=generate_password_hash(
                request.form["password"],
                method="pbkdf2:sha256"
            ),
            role="COMPANY"
        )

        db.session.add(user)
        db.session.commit()

        company = CompanyProfile(
            company_name=request.form["company_name"],
            hr_contact=request.form["hr_contact"],
            website=request.form["website"],
            user_id=user.id
        )

        db.session.add(company)
        db.session.commit()

        flash("Company registered. Await admin approval.", "info")
        return redirect(url_for("main.login"))

    return render_template("company_register.html")


# =========================================================
# ADMIN ROUTES
# =========================================================
@bp.route("/admin")
def admin_dashboard():

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    # ---------- Dashboard Statistics ----------
    stats = {
        "total_students": User.query.filter_by(role="STUDENT").count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count()
    }

    # ---------- Search Parameters ----------
    company_search = request.args.get("company_search", "")
    student_search = request.args.get("student_search", "")

    # ---------- Company Search ----------
    companies_query = CompanyProfile.query
    if company_search:
        companies_query = companies_query.filter(
            CompanyProfile.company_name.ilike(f"%{company_search}%")
        )
    companies = companies_query.all()

    # ---------- Student Search ----------
    students_query = User.query.filter_by(role="STUDENT")
    if student_search:
        students_query = students_query.filter(
            (User.full_name.ilike(f"%{student_search}%")) |
            (User.email.ilike(f"%{student_search}%")) |
            (User.id.ilike(f"%{student_search}%"))
        )
    students = students_query.all()

    drives = PlacementDrive.query.all()
    applications = Application.query.all()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        companies=companies,
        students=students,
        drives=drives,
        applications=applications
    )


@bp.route("/admin/company/<int:id>/approve")
def approve_company(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = "APPROVED"

    db.session.commit()
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:id>/approve")
def approve_drive(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = "APPROVED"

    db.session.commit()
    return redirect(url_for("main.admin_dashboard"))


# =========================================================
# ADMIN ACTIONS (Reject / Blacklist)
# =========================================================

@bp.route("/admin/company/<int:id>/reject")
def reject_company(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = "REJECTED"

    db.session.commit()
    flash("Company rejected", "warning")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/company/<int:id>/blacklist")
def blacklist_company(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.get_or_404(id)
    company.is_blacklisted = True  

    user = User.query.get(company.user_id)
    if user:
        user.is_active = False      

    db.session.commit()
    flash("Company blacklisted", "danger")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:id>/reject")
def reject_drive(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = "REJECTED"

    db.session.commit()
    flash("Placement drive rejected", "warning")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/student/<int:id>/blacklist")
def blacklist_student(id):

    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    student = User.query.get_or_404(id)
    student.is_active = False

    db.session.commit()
    flash("Student blacklisted", "danger")
    return redirect(url_for("main.admin_dashboard"))


# =========================================================
# COMPANY ROUTES
# =========================================================
@bp.route("/company")
def company_dashboard():

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    return render_template("company_dashboard.html", company=company)


@bp.route("/company/drive/create", methods=["GET", "POST"])
def create_drive():

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if company.approval_status != "APPROVED":
        flash("Company not approved yet", "danger")
        return redirect(url_for("main.company_dashboard"))

    if request.method == "POST":

        drive = PlacementDrive(
            job_title=request.form["title"],
            job_description=request.form["description"],
            eligibility_criteria=request.form["criteria"],
            application_deadline=request.form["deadline"],
            company_id=company.id
        )

        db.session.add(drive)
        db.session.commit()

        return redirect(url_for("main.company_dashboard"))

    return render_template("create_drive.html")


@bp.route("/company/application/<int:id>/<status>")
def update_application_status(id, status):

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    application = Application.query.get_or_404(id)
    application.status = status.upper()

    db.session.commit()
    return redirect(url_for("main.company_dashboard"))


# =========================================================
# STUDENT ROUTES
# =========================================================
@bp.route("/student")
def student_dashboard():

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    drives = PlacementDrive.query.filter_by(status="APPROVED").all()

    return render_template("student_dashboard.html", drives=drives)


@bp.route("/apply/<int:drive_id>")
def apply_drive(drive_id):

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    existing = Application.query.filter_by(
        student_id=session["user_id"],
        drive_id=drive_id
    ).first()

    if existing:
        flash("You have already applied", "warning")

    else:
        application = Application(
            student_id=session["user_id"],
            drive_id=drive_id
        )

        db.session.add(application)
        db.session.commit()
        flash("Application submitted", "success")

    return redirect(url_for("main.student_dashboard"))


@bp.route("/student/history")
def application_history():

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    applications = Application.query.filter_by(
        student_id=session["user_id"]
    ).order_by(Application.application_date.desc()).all()

    return render_template(
        "application_history.html",
        applications=applications
    )


@bp.route("/student/profile", methods=["GET", "POST"])
def student_profile():

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    user = User.query.get(session["user_id"])
    profile = StudentProfile.query.filter_by(user_id=user.id).first()

    if request.method == "POST":

        user.full_name = request.form.get("name")
        profile.qualification = request.form.get("qualification")
        profile.skills = request.form.get("skills")

        resume = request.files.get("resume")

        if resume:
            resume_path = f"resumes/{user.id}_{resume.filename}"
            resume.save(os.path.join("static", resume_path))
            profile.resume_path = resume_path

        db.session.commit()
        flash("Profile updated successfully", "success")

    return render_template(
        "student_profile.html",
        user=user,
        profile=profile
    )


# Expose bp for import
