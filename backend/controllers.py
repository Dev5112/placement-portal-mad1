from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from .models import Notification


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

            # 🔒 COMPANY APPROVAL CHECK (MANDATORY FIX)
            if user.role == "COMPANY":
                company = CompanyProfile.query.filter_by(user_id=user.id).first()

                if not company or company.approval_status != "APPROVED":
                    flash("Your company account is not approved by admin yet.", "warning")
                    return redirect(url_for("main.login"))

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
# STUDENT REGISTRATION (WITH RESUME UPLOAD)
# =========================================================
@bp.route("/student/register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        # ================= Check duplicate email =================
        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already exists", "warning")
            return redirect(url_for("main.student_register"))

        # ================= Create User =================
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

        # ================= Handle Resume Upload =================
        resume = request.files.get("resume")
        resume_path = None

        if resume and resume.filename != "":

            # Create folder if not exists
            upload_folder = os.path.join("static", "resumes")
            os.makedirs(upload_folder, exist_ok=True)

            # Secure filename
            from werkzeug.utils import secure_filename
            filename = secure_filename(resume.filename)

            # Save file
            filepath = os.path.join(upload_folder, filename)
            resume.save(filepath)

            # Store relative path in DB
            resume_path = f"resumes/{filename}"

        # ================= Create Student Profile =================
        profile = StudentProfile(
            qualification=request.form["qualification"],
            skills=request.form["skills"],
            resume_path=resume_path,
            user_id=user.id
        )

        db.session.add(profile)
        db.session.commit()

        flash("Student registered successfully", "success")
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
# ADMIN DASHBOARD
# =========================================================
@bp.route("/admin")
def admin_dashboard():
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    # ================= Stats =================
    stats = {
        "total_students": User.query.filter_by(role="STUDENT").count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count()
    }

    # ================= Search inputs =================
    company_search = request.args.get("company_search", "").strip()
    student_search = request.args.get("student_search", "").strip()

    # ================= Company Search =================
    companies = CompanyProfile.query
    if company_search:
        companies = companies.filter(
            CompanyProfile.company_name.ilike(f"%{company_search}%")
        )
    companies = companies.all()

    # ================= Student Search =================
    students = User.query.filter_by(role="STUDENT")
    if student_search:
        students = students.filter(
            (User.full_name.ilike(f"%{student_search}%")) |
            (User.email.ilike(f"%{student_search}%")) |
            (User.id.cast(db.String).ilike(f"%{student_search}%"))
        )
    students = students.all()

    # ================= Other Data =================
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

    flash("Company approved", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:id>/approve")
def approve_drive(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = "APPROVED"
    db.session.commit()

    flash("Drive approved", "success")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/student/<int:id>/blacklist")
def blacklist_student(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    student_user = User.query.get_or_404(id)

    # Disable student login
    student_user.is_active = False

    # Optional: mark profile blacklist (if you want tracking)
    student_profile = StudentProfile.query.filter_by(user_id=id).first()
    if student_profile:
        student_profile.is_blacklisted = True

    db.session.commit()

    flash("Student blacklisted successfully", "danger")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/student/<int:id>")
def admin_view_student(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    student = User.query.get_or_404(id)
    profile = StudentProfile.query.filter_by(user_id=id).first()
    applications = Application.query.filter_by(student_id=id).all()

    return render_template(
        "admin_view_student.html",
        student=student,
        profile=profile,
        applications=applications
    )

@bp.route("/admin/company/<int:id>/reject")
def reject_company(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = "REJECTED"
    db.session.commit()

    flash("Company rejected", "warning")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/company/<int:id>/blacklist", methods=["POST"])
def blacklist_company(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    reason = request.form.get("reason")

    company = CompanyProfile.query.get_or_404(id)
    message = ""
    if company.is_blacklisted:
        company.is_blacklisted = False
        company.blacklist_reason = None
        message = "Company unblacklisted successfully"
    else:
        company.is_blacklisted = True
        company.blacklist_reason = reason if reason else "No reason provided"
        message = "Company blacklisted successfully"

    user = User.query.get(company.user_id)
    if user:
        user.is_active = False

    db.session.commit()
    flash(message, "danger")

    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:id>/reject")
def reject_drive(id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = "REJECTED"
    db.session.commit()

    flash("Drive rejected successfully", "warning")
    return redirect(url_for("main.admin_dashboard"))


# COMPANY DASHBOARD
# =========================================================
@bp.route("/company")
def company_dashboard():
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first_or_404()

    drives = PlacementDrive.query.filter_by(
        company_id=company.id
    ).order_by(PlacementDrive.created_at.desc()).all()

    return render_template(
        "company_dashboard.html",
        company=company,
        drives=drives
    )

# CREATE PLACEMENT DRIVE
# =========================================================
@bp.route("/company/drive/create", methods=["GET", "POST"])
def create_drive():
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first_or_404()

    if company.approval_status != "APPROVED":
        flash("Company not approved yet", "danger")
        return redirect(url_for("main.company_dashboard"))

    if request.method == "POST":

        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        deadline_str = request.form.get("application_deadline")

        if not job_title or not job_description or not deadline_str:
            flash("All required fields must be filled", "danger")
            return redirect(url_for("main.create_drive"))

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        drive = PlacementDrive(
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=request.form.get("eligibility_criteria"),
            required_skills=request.form.get("required_skills"),
            experience_required=request.form.get("experience_required"),
            salary_range=request.form.get("salary_range"),
            application_deadline=deadline,
            company_id=company.id,
            status="PENDING" 
        )

        db.session.add(drive)
        db.session.commit()

        flash("Placement drive created successfully", "success")
        return redirect(url_for("main.company_dashboard"))

    return render_template("create_drive.html")


# CLOSE / MARK DRIVE AS COMPLETE
# =========================================================
@bp.route("/company/drive/<int:id>/close")
def close_drive(id):
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if drive.company_id != company.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for("main.company_dashboard"))

    drive.status = "CLOSED"
    db.session.commit()

    flash("Drive marked as complete", "success")
    return redirect(url_for("main.company_dashboard"))


# VIEW APPLICATIONS FOR A DRIVE
# =========================================================
@bp.route("/company/drive/<int:id>/applications")
def view_applications(id):
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if drive.company_id != company.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.company_dashboard"))

    applications = Application.query.filter_by(drive_id=id).all()

    return render_template(
        "company_applications.html",
        drive=drive,
        applications=applications
    )
@bp.route("/company/drive/<int:id>")
def view_drive(id):
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if drive.company_id != company.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.company_dashboard"))

    return render_template("company_view_drive.html", drive=drive)


# REVIEW SINGLE STUDENT APPLICATION
# =========================================================
@bp.route("/company/application/<int:id>")
def view_application(id):
    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    application = Application.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if application.placement_drive.company_id != company.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.company_dashboard"))

    return render_template(
        "company_view_application.html",
        application=application
    )
@bp.route("/company/drive/edit/<int:id>", methods=["GET", "POST"])
def edit_drive(id):

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if drive.company_id != company.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.company_dashboard"))

    if company.approval_status != "APPROVED":
        flash("You are not approved by admin yet.", "warning")
        return redirect(url_for("main.company_dashboard"))

    if request.method == "POST":

        drive.job_title = request.form.get("job_title")
        drive.job_description = request.form.get("job_description")
        drive.eligibility_criteria = request.form.get("eligibility_criteria")
        drive.required_skills = request.form.get("required_skills")
        drive.experience_required = request.form.get("experience_required")
        drive.salary_range = request.form.get("salary_range")

        deadline_str = request.form.get("application_deadline")
        drive.application_deadline = datetime.strptime(
            deadline_str, "%Y-%m-%d"
        ).date()

        db.session.commit()

        flash("Drive updated successfully!", "success")
        return redirect(url_for("main.company_dashboard"))

    return render_template(
        "company_edit_drive.html",
        drive=drive
    )

@bp.route("/company/drive/delete/<int:id>")
def delete_drive(id):

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    # 🔒 Ownership Check
    if drive.company_id != company.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.company_dashboard"))

    db.session.delete(drive)
    db.session.commit()

    flash("Drive deleted successfully!", "success")
    return redirect(url_for("main.company_dashboard"))

# UPDATE APPLICATION STATUS
# =========================================================
@bp.route("/company/application/<int:id>/<status>")
def update_application_status(id, status):

    if session.get("role") != "COMPANY":
        return redirect(url_for("main.login"))

    application = Application.query.get_or_404(id)
    company = CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

    if application.placement_drive.company_id != company.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for("main.company_dashboard"))

    # Update status
    application.status = status.upper()
    db.session.commit()

    # ✅ CREATE NOTIFICATION FOR STUDENT
    notification = Notification(
        student_id=application.student_id,
        message=f"Your application for '{application.placement_drive.job_title}' has been {application.status}."
    )

    db.session.add(notification)
    db.session.commit()

    flash("Application status updated", "success")

    return redirect(
        url_for("main.view_applications",
                id=application.drive_id)
    )

###-----Student Dashboard & Application Routes-----###

@bp.route("/student")
def student_dashboard():

    # -------------------------------
    # Role Check
    # -------------------------------
    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    student_id = session.get("user_id")
    if not student_id:
        return redirect(url_for("main.login"))

    today = datetime.utcnow().date()
    search = request.args.get("search", "").strip()

    from sqlalchemy.orm import joinedload

    # =====================================================
    # Available Drives (Approved + Not Expired)
    # =====================================================
    drives_query = PlacementDrive.query.options(
        joinedload(PlacementDrive.company)
    ).join(CompanyProfile).filter(
        PlacementDrive.status != None,
        PlacementDrive.application_deadline >= today,
        CompanyProfile.approval_status == "APPROVED",
        CompanyProfile.is_blacklisted.is_(False)
    )

    # 🔍 Search Filter
    if search:
        drives_query = drives_query.filter(
            (PlacementDrive.job_title.ilike(f"%{search}%")) |
            (PlacementDrive.required_skills.ilike(f"%{search}%")) |
            (CompanyProfile.company_name.ilike(f"%{search}%"))
        )

    drives = drives_query.order_by(
        PlacementDrive.application_deadline.asc()
    ).all()

    # =====================================================
    # My Applications (All)
    # =====================================================
    my_applications = Application.query.options(
        joinedload(Application.placement_drive).joinedload(PlacementDrive.company)
    ).filter_by(
        student_id=student_id
    ).all()

    # =====================================================
    # Placement History (Only Selected)
    # =====================================================
    placement_history = [
    app for app in my_applications if app.status in ["SELECTED", "PLACED"]
]

    # =====================================================
    # Notifications
    # =====================================================
    notifications = Notification.query.filter_by(
        student_id=student_id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    unread_count = Notification.query.filter_by(
        student_id=student_id,
        is_read=False
    ).count()

    # =====================================================
    # Render Template
    # =====================================================
    return render_template(
        "student_dashboard.html",
        drives=drives,
        my_applications=my_applications,
        placement_history=placement_history,
        notifications=notifications,
        unread_count=unread_count
    )


@bp.route("/student/drive/<int:drive_id>/apply")
def apply_drive(drive_id):

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(drive_id)

    # Check if already applied
    existing = Application.query.filter_by(
        drive_id=drive_id,
        student_id=session["user_id"]
    ).first()

    if existing:
        flash("You already applied to this drive.", "warning")
        return redirect(url_for("main.student_dashboard"))

    # Create new application
    new_application = Application(
        drive_id=drive_id,
        student_id=session["user_id"],
        status="APPLIED"
    )

    db.session.add(new_application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
    return redirect(url_for("main.student_dashboard"))


### ----- Student Profile Route ----- ###

@bp.route("/student/profile", methods=["GET", "POST"])
def student_profile():

    if session.get("role") != "STUDENT":
        return redirect(url_for("main.login"))

    student_id = session.get("user_id")
    if not student_id:
        return redirect(url_for("main.login"))

    user = User.query.get_or_404(student_id)
    profile = StudentProfile.query.filter_by(user_id=student_id).first()

    if request.method == "POST":
        user.full_name = request.form.get("name")
        profile.qualification = request.form.get("qualification")
        profile.skills = request.form.get("skills")

        # ================= Resume Upload =================
        file = request.files.get("resume")

        if file and file.filename != "":
            # Make filename unique (prevents overwrite)
            unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"

            # IMPORTANT: Use absolute path from app root
            upload_folder = os.path.join(current_app.root_path, "static", "resumes")
            os.makedirs(upload_folder, exist_ok=True)

            filepath = os.path.join(upload_folder, unique_filename)
            file.save(filepath)

            # Store only relative path in DB
            profile.resume_path = f"resumes/{unique_filename}"

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("main.student_profile"))

    return render_template(
        "student_profile.html",
        user=user,
        profile=profile
    )

@bp.route("/student/notifications/read")
def mark_notifications_read():
    student_id = session.get("user_id")

    Notification.query.filter_by(
        student_id=student_id,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()

    return redirect(url_for("main.student_dashboard"))

