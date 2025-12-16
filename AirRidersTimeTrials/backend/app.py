import os
import re
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import Config
from extensions import db, ma, jwt


from routes_main import bp_home

from routes_countries import bp_countries, load_countries_from_json
from routes_auth import bp_auth
from routes_courses import bp_courses
from routes_records import bp_records

from models import Course, Machine, Character
from seed import run_seed


# ---------- helpers for auto-seeding ----------
def project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def static_images_dir(*parts) -> str:
    return os.path.join(project_root(), "static", "images", *parts)

def list_image_files(folder: str):
    if not os.path.isdir(folder):
        return []
    out = []
    for f in os.listdir(folder):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            out.append(f)
    return sorted(out)

def prettify_name_from_filename(filename: str) -> str:
    """
    Turns filenames like:
      KARs_Meta_Knight_icon.png -> Meta Knight
      KARs_Warp_Star_Icon.png   -> Warp Star
      Floria_Fields.png         -> Floria Fields
    """
    base = os.path.splitext(filename)[0]

    # strip common prefixes/suffixes used in your packs
    base = re.sub(r"^KARs_", "", base)
    base = re.sub(r"_icon$", "", base, flags=re.IGNORECASE)
    base = re.sub(r"_Icon$", "", base, flags=re.IGNORECASE)

    # replace underscores with spaces
    base = base.replace("_", " ").strip()

    # normalize double spaces
    base = re.sub(r"\s+", " ", base)

    return base

def slugify_course_key(name: str) -> str:
    """
    "Floria Fields" -> "floria-fields"
    """
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s


def seed_all_courses():
    """
    Seeds ALL courses from your project list.
    Also tries to find a matching map icon file in static/images/mapICONS/
    by checking common filename variants.
    """
    air_ride_courses = [
        "Floria Fields", "Waveflow Waters", "Airtopia Ruins", "Crystalline Fissure",
        "Steamgust Forge", "Cavernous Corners", "Cyberion Highway", "Mount Amberfalls",
        "Galactic Nova", "Fantasy Meadows", "Celestial Valley", "Sky Sands",
        "Frozen Hillside", "Magma Flows", "Beanstalk Park", "Machine Passage",
        "Checker Knights", "Nebula Belt"
    ]

    top_ride_courses = [
        "Flower", "Flow", "Air", "Crystal", "Steam", "Cave", "Cyber", "Mountain", "Nova"
    ]

    map_folder = static_images_dir("mapICONS")
    map_files = set(list_image_files(map_folder))

    def find_map_icon(course_name: str):
        """
        Looks for icon files using a few likely naming conventions.
        Returns a relative path (under /static) like: "images/mapICONS/Floria_Fields.png"
        or None if not found.
        """
        candidates = [
            course_name.replace(" ", "_") + ".png",
            # sometimes people keep spaces in filenames
            course_name + ".png",
        ]
        for c in candidates:
            if c in map_files:
                return f"images/mapICONS/{c}"
        return None

    # insert if missing
    for name in air_ride_courses:
        key = slugify_course_key(name)
        existing = Course.query.filter_by(course_key=key).first()
        if not existing:
            db.session.add(Course(
                course_key=key,
                name=name,
                map_icon=find_map_icon(name)
            ))
        else:
            # update icon if empty and file exists
            if not existing.map_icon:
                icon = find_map_icon(name)
                if icon:
                    existing.map_icon = icon

    for name in top_ride_courses:
        display_name = f"{name} (Top Ride)"
        key = slugify_course_key(name)  # user asked "flower", "flow", etc. keep keys simple
        existing = Course.query.filter_by(course_key=key).first()
        if not existing:
            db.session.add(Course(
                course_key=key,
                name=display_name,
                map_icon=find_map_icon(name)  # expects Flower.png, Flow.png, etc.
            ))
        else:
            if not existing.map_icon:
                icon = find_map_icon(name)
                if icon:
                    existing.map_icon = icon

    db.session.commit()


def seed_all_characters_from_icons():
    """
    Seeds characters from whatever is inside static/images/charICONS/
    """
    folder = static_images_dir("charICONS")
    for fname in list_image_files(folder):
        name = prettify_name_from_filename(fname)
        rel_icon = f"images/charICONS/{fname}"

        existing = Character.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Character(name=name, icon=rel_icon))
        else:
            # keep icon path fresh if file changed
            existing.icon = rel_icon

    db.session.commit()


def seed_all_machines_from_icons():
    """
    Seeds machines from whatever is inside static/images/machineICONS/
    """
    folder = static_images_dir("machineICONS")
    for fname in list_image_files(folder):
        name = prettify_name_from_filename(fname)
        rel_icon = f"images/machineICONS/{fname}"

        existing = Machine.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Machine(name=name, icon=rel_icon))
        else:
            existing.icon = rel_icon

    db.session.commit()


def create_app():
    app = Flask(__name__, static_folder="../static", static_url_path="/static")
    app.config.from_object(Config)
    CORS(app)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    # Blueprints
    app.register_blueprint(bp_home)
    
    app.register_blueprint(bp_countries)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_courses)
    app.register_blueprint(bp_records)

    # Serve uploaded proof files
    @app.get("/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    with app.app_context():
        db.create_all()

        # Countries from countries.json → DB (once)
        load_countries_from_json()

        # Auto seed EVERYTHING from static folders + course list
        seed_all_courses()
        seed_all_characters_from_icons()
        seed_all_machines_from_icons()

        
        run_seed()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5500)
