import json
import os
from flask import Blueprint, jsonify
from extensions import db
from models import Country

bp_countries = Blueprint("countries", __name__)

@bp_countries.get("/api/countries")
def get_countries():
    countries = Country.query.order_by(Country.name.asc()).all()
    return jsonify([{"code": c.code, "name": c.name} for c in countries])

def load_countries_from_json():
    """
    Your countries.json is a dict:
      { "US": "United States", "JP": "Japan", ... }

    We store codes lowercased so they match your svg filenames:
      us -> static/images/country-flags-main/svg/us.svg
    """
    if Country.query.first():
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(base_dir, "static", "images", "country-flags-main", "countries.json")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"countries.json not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("countries.json must be a JSON object/dict of {CODE: Name}")

    for code, name in data.items():
        code = (code or "").lower().strip()
        name = (name or "").strip()
        if len(code) >= 2 and name:
            # keep only first 2 letters for true ISO-2 entries
            # and skip weird ones like GB-ENG if you want:
            if len(code) != 2:
                continue

            db.session.add(Country(code=code, name=name))

    db.session.commit()
