from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User
from schemas import RegisterSchema, LoginSchema, UpdateUserSchema

bp_auth = Blueprint("auth", __name__)

@bp_auth.post("/api/register")
def register():
    payload = request.get_json(force=True)
    data = RegisterSchema().load(payload)

    username = data["username"].strip()
    password = data["password"]
    country_code = (data.get("country_code") or None)
    if country_code:
        country_code = country_code.lower()

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        country_code=country_code
    )
    db.session.add(user)
    db.session.commit()

#changed the tokens to strings
    #token = create_access_token(identity=user.id)
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": {"username": user.username, "country_code": user.country_code}}), 201

@bp_auth.post("/api/login")
def login():
    payload = request.get_json(force=True)
    data = LoginSchema().load(payload)

    user = User.query.filter_by(username=data["username"].strip()).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid username or password."}), 401

    #changed the tokens to strings
    #token = create_access_token(identity=user.id)
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": {"username": user.username, "country_code": user.country_code}})

@bp_auth.get("/api/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"username": user.username, "country_code": user.country_code})

@bp_auth.patch("/api/me")
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    payload = request.get_json(force=True)

    try:
        data = UpdateUserSchema().load(payload)
    except Exception as e:
        print("DEBUG VALIDATION ERROR:", e.messages if hasattr(e, 'messages') else str(e)) #CHANGE THIS LATER FIXME
        return jsonify({"error": str(e.messages if hasattr(e, 'messages') else e)}), 422
    
    if "country_code" in data:
        code = data["country_code"]
        user.country_code = code.lower() if code else None

    db.session.commit()

    return jsonify({"username": user.username, 
                    "country_code": user.country_code})

#this is the part where it deletes the user
@bp_auth.delete("/api/me")
@jwt_required()
def delete_me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete account"}), 500