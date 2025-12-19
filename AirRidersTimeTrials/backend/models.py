from datetime import datetime
from extensions import db

class Country(db.Model):
    __tablename__ = "countries"
    code = db.Column(db.String(2), primary_key=True)  # "us"
    name = db.Column(db.String(120), nullable=False)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    course_key = db.Column(db.String(64), unique=True, nullable=False)  # "floria-fields"
    name = db.Column(db.String(120), nullable=False)
    map_icon = db.Column(db.String(255), nullable=True)  # "images/mapICONS/Floria_Fields.png"

class Machine(db.Model):
    __tablename__ = "machines"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    icon = db.Column(db.String(255), nullable=False)  # "images/machineICONS/KARs_Warp_Star_Icon.png"

class Character(db.Model):
    __tablename__ = "characters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    icon = db.Column(db.String(255), nullable=False)  # "images/charICONS/KARs_Kirby_icon.png"

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    country_code = db.Column(db.String(2), db.ForeignKey("countries.code"), nullable=True)

    country = db.relationship("Country")

    #deletes the users records along with user acct being deleted
    records = db.relationship("Record", back_populates="user", cascade="all, delete-orphan")

class Record(db.Model):
    __tablename__ = "records"
    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    time_str = db.Column(db.String(32), nullable=False)  # "1'05\"780"
    time_ms = db.Column(db.Integer, nullable=False)      # for sorting / WR calculation

    date_set = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    lap1 = db.Column(db.Float, nullable=True)
    lap2 = db.Column(db.Float, nullable=True)
    lap3 = db.Column(db.Float, nullable=True)

    proof_url = db.Column(db.String(255), nullable=False)  # "/uploads/abc.mp4"

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course")
    machine = db.relationship("Machine")
    character = db.relationship("Character")
    user = db.relationship("User", back_populates="records")
