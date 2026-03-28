from flask import Blueprint, jsonify, request
from backend.models import db, User, CompanyProfile, StudentProfile, PlacementDrive, Application

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
