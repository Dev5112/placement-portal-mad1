from flask import Blueprint, jsonify, request
from backend.models import db, User, CompanyProfile, StudentProfile, PlacementDrive, Application
from sqlalchemy import func

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ==========================================
# 1. GET ALL USERS (GET)
# ==========================================
@api_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        })
    return jsonify({"status": "success", "data": user_list}), 200

# ==========================================
# 2. CREATE A JOB DRIVE (POST)
# ==========================================
@api_bp.route("/drives", methods=["POST"])
def create_drive():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
        
    required_fields = ["job_title", "job_description", "company_id", "application_deadline"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
            
    try:
        from datetime import datetime
        deadline = datetime.strptime(data["application_deadline"], "%Y-%m-%d").date()
        
        drive = PlacementDrive(
            job_title=data["job_title"],
            job_description=data["job_description"],
            eligibility_criteria=data.get("eligibility_criteria", ""),
            required_skills=data.get("required_skills", ""),
            experience_required=data.get("experience_required"),
            salary_range=data.get("salary_range", ""),
            application_deadline=deadline,
            company_id=data["company_id"],
            status="PENDING"
        )
        db.session.add(drive)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Drive created", "drive_id": drive.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# 3. UPDATE APPLICATION STATUS (PUT)
# ==========================================
@api_bp.route("/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id):
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Missing 'status' in JSON body"}), 400
        
    application = Application.query.get(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
        
    application.status = data["status"]
    db.session.commit()
    return jsonify({"status": "success", "message": f"Application status updated to {data['status']}"}), 200

# ==========================================
# 4. DELETE A JOB DRIVE (DELETE)
# ==========================================
@api_bp.route("/drives/<int:drive_id>", methods=["DELETE"])
def delete_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
        
    db.session.delete(drive)
    db.session.commit()
    return jsonify({"status": "success", "message": "Drive deleted successfully"}), 200

# ==========================================
# 5. CHARTS API (ADMIN)
# ==========================================
@api_bp.route("/stats/admin", methods=["GET"])
def admin_stats():
    total_postings = PlacementDrive.query.count()
    total_applications = Application.query.count()
    total_placements = Application.query.filter(Application.status.in_(["SELECTED", "PLACED"])).count()
    return jsonify({
        "job_postings": total_postings,
        "applications": total_applications,
        "placements": total_placements
    }), 200

# ==========================================
# 6. CHARTS API (COMPANY)
# ==========================================
@api_bp.route("/stats/company/<int:company_id>", methods=["GET"])
def company_stats(company_id):
    # Number of applications per published drive by this company
    drives = PlacementDrive.query.filter_by(company_id=company_id).all()
    labels = []
    data = []
    for d in drives:
        labels.append(d.job_title[:15] + "...") # truncate
        count = Application.query.filter_by(drive_id=d.id).count()
        data.append(count)
    return jsonify({"labels": labels, "data": data}), 200

# ==========================================
# 7. CHARTS API (STUDENT)
# ==========================================
@api_bp.route("/stats/student/<int:student_id>", methods=["GET"])
def student_stats(student_id):
    # Application distribution by status
    stats = db.session.query(Application.status, func.count(Application.id)).filter_by(student_id=student_id).group_by(Application.status).all()
    labels = []
    data = []
    for s in stats:
        labels.append(s[0])
        data.append(s[1])
    return jsonify({"labels": labels, "data": data}), 200
