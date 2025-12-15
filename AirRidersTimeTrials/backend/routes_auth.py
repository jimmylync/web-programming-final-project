from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User
from schemas import RegisterSchema, LoginSchema

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

    token = create_access_token(identity=user.id)
    return jsonify({"access_token": token, "user": {"username": user.username, "country_code": user.country_code}}), 201

@bp_auth.post("/api/login")
def login():
    payload = request.get_json(force=True)
    data = LoginSchema().load(payload)

    user = User.query.filter_by(username=data["username"].strip()).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid username or password."}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"access_token": token, "user": {"username": user.username, "country_code": user.country_code}})

@bp_auth.get("/api/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    return jsonify({"username": user.username, "country_code": user.country_code})

@bp_auth.patch("/api/me")
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    payload = request.get_json(force=True)
    # keep it minimal: only country for now
    country_code = payload.get("country_code")
    if country_code is not None:
        user.country_code = country_code.lower().strip() or None

    db.session.commit()
    return jsonify({"username": user.username, "country_code": user.country_code})
