import os
import random
from datetime import date, timedelta

from faker import Faker
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, Course, Machine, Character, Record, Country
from schemas import parse_time_to_ms

fake = Faker()

# --- tweak these knobs ---
DEFAULT_PASSWORD = "password123"
USERS_TO_CREATE = 50
HISTORY_PER_COURSE_MACHINE = 3   # how many records per course+machine
AIR_RIDE_TIME_RANGE = (55.0, 150.0)  # seconds (min, max)
TOP_RIDE_TIME_RANGE = (18.0, 60.0)   # seconds (min, max)


def ensure_placeholder_proof(upload_folder: str) -> str:
    """
    Ensures uploads/placeholder.png exists so seeded records have a valid proof_url.
    Returns the URL string stored in DB.
    """
    os.makedirs(upload_folder, exist_ok=True)
    placeholder_path = os.path.join(upload_folder, "placeholder.png")
    if not os.path.exists(placeholder_path):
        # tiny valid PNG (1x1) as bytes — no extra libs needed
        png_1x1 = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x02"
            b"\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with open(placeholder_path, "wb") as f:
            f.write(png_1x1)

    return "/uploads/placeholder.png"


def rand_time_str(seconds_min: float, seconds_max: float) -> str:
    """
    Generates a time string formatted like: M'SS"mmm
    """
    total = random.uniform(seconds_min, seconds_max)
    minutes = int(total // 60)
    seconds = int(total % 60)
    millis = int(round((total - int(total)) * 1000)) % 1000
    return f"{minutes}'{seconds:02d}\"{millis:03d}"


def split_laps_from_total_ms(total_ms: int, laps: int = 3):
    """
    Splits total_ms into 3 laps that sum ~ total_ms.
    Returns floats in seconds with 3 decimals.
    """
    if laps != 3:
        raise ValueError("This project currently assumes 3-lap splits.")

    # Create two cut points around 1/3 and 2/3 with random variation
    a = int(total_ms * random.uniform(0.30, 0.36))
    b = int(total_ms * random.uniform(0.63, 0.70))
    lap1 = a
    lap2 = b - a
    lap3 = total_ms - b

    # convert to seconds
    return (round(lap1 / 1000.0, 3), round(lap2 / 1000.0, 3), round(lap3 / 1000.0, 3))


def pick_country_codes():
    """
    Pull all country codes from the DB once and return a list.
    """
    codes = [c.code for c in Country.query.all()]
    # fallback if somehow empty
    return codes or ["us", "jp", "ca"]


def seed_users(n=USERS_TO_CREATE):
    """
    Creates N users with random country codes.
    """
    country_codes = pick_country_codes()
    users = []

    # ensure uniqueness
    seen = set()

    for _ in range(n):
        # keep trying until we get a unique username
        username = None
        while not username or username in seen or User.query.filter_by(username=username).first():
            username = fake.user_name() + str(random.randint(10, 9999))
        seen.add(username)

        user = User(
            username=username,
            password_hash=generate_password_hash(DEFAULT_PASSWORD),
            country_code=random.choice(country_codes)
        )
        db.session.add(user)
        users.append(user)

    db.session.commit()
    return users


def is_top_ride_course(course: Course) -> bool:
    """
    We seeded Top Ride courses with names like "Flower (Top Ride)".
    Keys are plain "flower", "flow", etc.
    """
    return "(Top Ride)" in (course.name or "")


def seed_records(users, proof_url: str, per_course_machine=HISTORY_PER_COURSE_MACHINE):
    """
    Creates multiple records per course+machine spread across users and characters.
    """
    courses = Course.query.all()
    machines = Machine.query.all()
    characters = Character.query.all()

    if not courses or not machines or not characters:
        print("Seed records skipped: missing courses/machines/characters.")
        return

    for course in courses:
        for machine in machines:
            # Create several records over time (history)
            for _ in range(per_course_machine):
                u = random.choice(users)
                ch = random.choice(characters)

                # choose time range based on course type
                if is_top_ride_course(course):
                    t = rand_time_str(*TOP_RIDE_TIME_RANGE)
                else:
                    t = rand_time_str(*AIR_RIDE_TIME_RANGE)

                total_ms = parse_time_to_ms(t)

                # laps (optional but nice for display)
                lap1, lap2, lap3 = split_laps_from_total_ms(total_ms)

                rec = Record(
                    course_id=course.id,
                    machine_id=machine.id,
                    character_id=ch.id,
                    user_id=u.id,
                    time_str=t,
                    time_ms=total_ms,
                    date_set=date.today() - timedelta(days=random.randint(1, 500)),
                    lap1=lap1,
                    lap2=lap2,
                    lap3=lap3,
                    proof_url=proof_url
                )
                db.session.add(rec)

    db.session.commit()


def run_seed(upload_folder: str = None):
    """
    Main seed entrypoint.
    Safe: won't reseed if records already exist.
    """
    from flask import current_app

    # If we already have records, don't spam duplicates
    if Record.query.first():
        print("Seed skipped: records already exist.")
        return

    # Determine upload folder (from config if possible)
    if upload_folder is None:
        upload_folder = current_app.config.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))

    proof_url = ensure_placeholder_proof(upload_folder)

    # If users already exist, reuse them; otherwise create 50.
    users = User.query.all()
    if not users:
        users = seed_users(USERS_TO_CREATE)

    seed_records(users, proof_url, per_course_machine=HISTORY_PER_COURSE_MACHINE)
    print(f"Seed complete: {len(users)} users; records generated across all courses & machines.")
