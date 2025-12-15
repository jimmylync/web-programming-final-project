import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Course, Machine, Character, Record, User
from schemas import RecordCreateSchema, parse_time_to_ms

bp_records = Blueprint("records", __name__)

def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_PROOF_EXTENSIONS"]

@bp_records.post("/api/records")
@jwt_required()
def create_record():
    """
    multipart/form-data:
      fields: course_key, machine_name, character_name, time, lap1, lap2, lap3
      file: proof
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    # Validate text fields
    form_data = {
        "course_key": request.form.get("course_key"),
        "machine_name": request.form.get("machine_name"),
        "character_name": request.form.get("character_name"),
        "time": request.form.get("time"),
        "lap1": request.form.get("lap1") or None,
        "lap2": request.form.get("lap2") or None,
        "lap3": request.form.get("lap3") or None,
    }

    # Convert lap strings to float safely
    for k in ["lap1", "lap2", "lap3"]:
        if form_data[k] is not None:
            try:
                form_data[k] = float(form_data[k])
            except ValueError:
                return jsonify({"error": f"{k} must be a number"}), 400

    data = RecordCreateSchema().load(form_data)

    # Validate file
    if "proof" not in request.files:
        return jsonify({"error": "Proof file is required"}), 400
    proof = request.files["proof"]
    if proof.filename == "":
        return jsonify({"error": "Proof file is required"}), 400
    if not allowed_file(proof.filename):
        return jsonify({"error": "Unsupported proof file type"}), 400

    course = Course.query.filter_by(course_key=data["course_key"]).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404

    machine = Machine.query.filter_by(name=data["machine_name"]).first()
    if not machine:
        return jsonify({"error": "Machine not found"}), 404

    character = Character.query.filter_by(name=data["character_name"]).first()
    if not character:
        return jsonify({"error": "Character not found"}), 404

    # Save file
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    safe_name = secure_filename(proof.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)

    # Avoid overwriting
    base, ext = os.path.splitext(safe_name)
    i = 1
    while os.path.exists(save_path):
        safe_name = f"{base}_{i}{ext}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
        i += 1

    proof.save(save_path)
    proof_url = f"/uploads/{safe_name}"

    # Insert record
    time_ms = parse_time_to_ms(data["time"])
    rec = Record(
        course_id=course.id,
        machine_id=machine.id,
        character_id=character.id,
        user_id=user.id,
        time_str=data["time"],
        time_ms=time_ms,
        lap1=data.get("lap1"),
        lap2=data.get("lap2"),
        lap3=data.get("lap3"),
        proof_url=proof_url
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"ok": True, "record_id": rec.id, "proof_url": rec.proof_url}), 201
