import os
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, and_

from extensions import db
from models import Course, Machine, Character, Record, User
from schemas import RecordCreateSchema, parse_time_to_ms

bp_records = Blueprint("records", __name__)

# -------------------- HELPERS --------------------
def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_PROOF_EXTENSIONS"]

def days_since(d: date | None) -> int:
    if not d:
        return 0
    return max(0, (date.today() - d).days)

def _record_to_row(rec: Record):
    """Shared serializer for record rows used by multiple endpoints."""
    user = rec.user
    course = rec.course
    machine = rec.machine
    char = rec.character
    nation = (user.country_code or "us").lower()

    return {
        "record_id": rec.id,
        "course_key": course.course_key,
        "course_name": course.name,
        "machine_name": machine.name,
        "machine_icon": machine.icon,
        "time": rec.time_str,
        "player": user.username,
        "nation_code": nation,
        "date": rec.date_set.isoformat() if rec.date_set else None,
        "days": days_since(rec.date_set),
        "lap1": rec.lap1,
        "lap2": rec.lap2,
        "lap3": rec.lap3,
        "char_name": char.name,
        "char_icon": char.icon,
        "proof_url": rec.proof_url,
    }

def _current_machine_wrs_query():
    """
    Returns a query that yields the CURRENT best record for each (course_id, machine_id),
    based on min(time_ms). Ties are broken by earliest date_set then lowest id.
    """
    sub = (
        db.session.query(
            Record.course_id.label("course_id"),
            Record.machine_id.label("machine_id"),
            func.min(Record.time_ms).label("min_ms"),
        )
        .group_by(Record.course_id, Record.machine_id)
        .subquery()
    )

    q = (
        db.session.query(Record)
        .join(
            sub,
            and_(
                Record.course_id == sub.c.course_id,
                Record.machine_id == sub.c.machine_id,
                Record.time_ms == sub.c.min_ms,
            ),
        )
        .order_by(Record.date_set.asc(), Record.id.asc())
    )

    return q

def _pick_one_per_group(records, key_fn):
    """If ties come back from SQL, pick the first per group (we already ordered)."""
    out = {}
    for r in records:
        k = key_fn(r)
        if k not in out:
            out[k] = r
    return list(out.values())

# -------------------- UPLOAD --------------------
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

    form_data = {
        "course_key": request.form.get("course_key"),
        "machine_name": request.form.get("machine_name"),
        "character_name": request.form.get("character_name"),
        "time": request.form.get("time"),
        "lap1": request.form.get("lap1") or None,
        "lap2": request.form.get("lap2") or None,
        "lap3": request.form.get("lap3") or None,
    }

    for k in ["lap1", "lap2", "lap3"]:
        if form_data[k] is not None:
            try:
                form_data[k] = float(form_data[k])
            except ValueError:
                return jsonify({"error": f"{k} must be a number"}), 400

    data = RecordCreateSchema().load(form_data)

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

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    safe_name = secure_filename(proof.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)

    base, ext = os.path.splitext(safe_name)
    i = 1
    while os.path.exists(save_path):
        safe_name = f"{base}_{i}{ext}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
        i += 1

    proof.save(save_path)
    proof_url = f"/uploads/{safe_name}"

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
        proof_url=proof_url,
        date_set=date.today(),  # you can also accept from form later if needed
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"ok": True, "record_id": rec.id, "proof_url": rec.proof_url}), 201

# -------------------- STATS: HOME "Current WRs" --------------------
@bp_records.get("/api/current-wrs")
def current_wrs_best_per_course():
    """
    Best time per COURSE (1 row each course).
    Used by: Home "Current WRs" table.
    """
    sub = (
        db.session.query(
            Record.course_id.label("course_id"),
            func.min(Record.time_ms).label("min_ms"),
        )
        .group_by(Record.course_id)
        .subquery()
    )

    q = (
        db.session.query(Record)
        .join(sub, and_(Record.course_id == sub.c.course_id, Record.time_ms == sub.c.min_ms))
        .order_by(Record.date_set.asc(), Record.id.asc())
        .all()
    )

    best = _pick_one_per_group(q, lambda r: r.course_id)
    # Nice ordering by course name:
    best.sort(key=lambda r: (r.course.name or "").lower())

    return jsonify([{
        "course_key": r.course.course_key,
        "course_name": r.course.name,
        "machine_name": r.machine.name,
        "machine_icon": r.machine.icon,
        "time": r.time_str,
        "player": r.user.username,
        "nation_code": (r.user.country_code or "us").lower(),
        "date": r.date_set.isoformat() if r.date_set else None,
        "char_icon": r.character.icon,
    } for r in best])

# -------------------- STATS: WR Snapshot --------------------
@bp_records.get("/api/wr-snapshot")
def wr_snapshot_best_per_course_machine():
    """
    Best time per (COURSE + MACHINE).
    Used by: WR Snapshot page.
    """
    current = _current_machine_wrs_query().all()
    current = _pick_one_per_group(current, lambda r: (r.course_id, r.machine_id))

    # order by course then machine
    current.sort(key=lambda r: ((r.course.name or "").lower(), (r.machine.name or "").lower()))

    return jsonify([{
        "course_key": r.course.course_key,
        "course_name": r.course.name,
        "machine_name": r.machine.name,
        "machine_icon": r.machine.icon,
        "time": r.time_str,
        "player": r.user.username,
        "nation_code": (r.user.country_code or "us").lower(),
        "date": r.date_set.isoformat() if r.date_set else None,
    } for r in current])

# -------------------- STATS: Recent WRs (last N days) --------------------
@bp_records.get("/api/recent-wrs")
def recent_wrs():
    """
    Current WRs that were set in the last N days (defaults 5).
    Used by: Recent WRs page.
    """
    try:
        days = int(request.args.get("days", 5))
    except ValueError:
        days = 5

    cutoff = date.today() - timedelta(days=days)

    current = _current_machine_wrs_query().filter(Record.date_set >= cutoff).all()
    current = _pick_one_per_group(current, lambda r: (r.course_id, r.machine_id))
    current.sort(key=lambda r: (r.date_set or date.min), reverse=True)

    return jsonify([{
        "date": r.date_set.isoformat() if r.date_set else None,
        "course_name": r.course.name,
        "course_key": r.course.course_key,
        "machine_name": r.machine.name,
        "machine_icon": r.machine.icon,
        "time": r.time_str,
        "player": r.user.username,
        "nation_code": (r.user.country_code or "us").lower(),
        "char_icon": r.character.icon,
    } for r in current])

# -------------------- RANKINGS: Players --------------------
@bp_records.get("/api/rankings/players")
def rankings_players():
    """
    Rankings by CURRENT WRs held:
      - wr_count: number of current (course,machine) WRs held by player
      - total_wr_days: sum of days since date_set for those WRs
    """
    current = _current_machine_wrs_query().all()
    current = _pick_one_per_group(current, lambda r: (r.course_id, r.machine_id))

    agg = {}
    for r in current:
        uid = r.user_id
        if uid not in agg:
            agg[uid] = {
                "player": r.user.username,
                "nation_code": (r.user.country_code or "us").lower(),
                "wr_count": 0,
                "total_wr_days": 0,
            }
        agg[uid]["wr_count"] += 1
        agg[uid]["total_wr_days"] += days_since(r.date_set)

    rows = list(agg.values())
    rows.sort(key=lambda x: (x["wr_count"], x["total_wr_days"]), reverse=True)

    out = []
    for i, row in enumerate(rows, start=1):
        out.append({
            "rank": i,
            **row
        })
    return jsonify(out)

# -------------------- RANKINGS: Countries --------------------
@bp_records.get("/api/rankings/countries")
def rankings_countries():
    """
    Rankings by CURRENT WRs held by country:
      - wr_count: number of current WRs whose holder has that country_code
      - unique_players: unique users contributing to that country in current WRs
    """
    current = _current_machine_wrs_query().all()
    current = _pick_one_per_group(current, lambda r: (r.course_id, r.machine_id))

    agg = {}
    for r in current:
        code = (r.user.country_code or "us").lower()
        if code not in agg:
            agg[code] = {"nation_code": code, "wr_count": 0, "players": set()}
        agg[code]["wr_count"] += 1
        agg[code]["players"].add(r.user_id)

    rows = [{
        "nation_code": k,
        "wr_count": v["wr_count"],
        "unique_players": len(v["players"]),
    } for k, v in agg.items()]

    rows.sort(key=lambda x: (x["wr_count"], x["unique_players"]), reverse=True)

    out = []
    for i, row in enumerate(rows, start=1):
        out.append({"rank": i, **row})
    return jsonify(out)

# -------------------- COURSE PAGE --------------------
@bp_records.get("/api/course/<course_key>")
def course_view(course_key: str):
    course = Course.query.filter_by(course_key=course_key).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # current WR per machine for this course
    sub = (
        db.session.query(
            Record.machine_id.label("machine_id"),
            func.min(Record.time_ms).label("min_ms"),
        )
        .filter(Record.course_id == course.id)
        .group_by(Record.machine_id)
        .subquery()
    )

    cur_rows = (
        db.session.query(Record)
        .join(sub, and_(Record.machine_id == sub.c.machine_id, Record.time_ms == sub.c.min_ms))
        .filter(Record.course_id == course.id)
        .order_by(Record.date_set.asc(), Record.id.asc())
        .all()
    )
    cur_rows = _pick_one_per_group(cur_rows, lambda r: r.machine_id)
    cur_rows.sort(key=lambda r: (r.machine.name or "").lower())

    currentMachineWrs = []
    for r in cur_rows:
        currentMachineWrs.append({
            "machineName": r.machine.name,
            "machineIcon": r.machine.icon,
            "date": r.date_set.isoformat() if r.date_set else None,
            "time": r.time_str,
            "player": r.user.username,
            "nationCode": (r.user.country_code or "us").lower(),
            "days": days_since(r.date_set),
            "lap1": r.lap1,
            "lap2": r.lap2,
            "lap3": r.lap3,
            "charIcon": r.character.icon,
            "charAlt": r.character.name,
            "proofUrl": r.proof_url,
        })

    # history: all records for this course ordered newest first
    hist = (
        Record.query
        .filter_by(course_id=course.id)
        .order_by(Record.date_set.desc(), Record.id.desc())
        .all()
    )

    history = []
    for r in hist:
        history.append({
            "date": r.date_set.isoformat() if r.date_set else None,
            "machineName": r.machine.name,
            "machineIcon": r.machine.icon,
            "time": r.time_str,
            "player": r.user.username,
            "nationCode": (r.user.country_code or "us").lower(),
            "days": days_since(r.date_set),
            "lap1": r.lap1,
            "lap2": r.lap2,
            "lap3": r.lap3,
            "charIcon": r.character.icon,
            "proofUrl": r.proof_url,
        })

    # simple summary (matches your UI)
    summary = {
        "totalMachineWrs": len(currentMachineWrs),
        "uniquePlayers": len(set([r["player"] for r in currentMachineWrs])),
        "uniqueNations": len(set([r["nationCode"] for r in currentMachineWrs])),
        "uniqueMachines": len(set([r["machineName"] for r in currentMachineWrs])),
    }

    # stats tables inside course panel (optional but keeps your UI filled)
    # player -> total days
    player_days = {}
    machine_days = {}
    nation_count = {}

    for r in currentMachineWrs:
        player_days[r["player"]] = player_days.get(r["player"], 0) + (r["days"] or 0)
        machine_days[r["machineName"]] = machine_days.get(r["machineName"], 0) + (r["days"] or 0)
        nation_count[r["nationCode"]] = nation_count.get(r["nationCode"], 0) + 1

    total_days_all = sum(player_days.values()) or 1

    stats_by_player = [{
        "player": p,
        "totalDays": d,
        "pct": round((d / total_days_all) * 100, 2)
    } for p, d in sorted(player_days.items(), key=lambda x: x[1], reverse=True)]

    stats_by_machine = [{
        "machine": m,
        "totalDays": d,
        "pct": round((d / total_days_all) * 100, 2)
    } for m, d in sorted(machine_days.items(), key=lambda x: x[1], reverse=True)]

    stats_by_nation = [{
        "nation": n,
        "count": c
    } for n, c in sorted(nation_count.items(), key=lambda x: x[1], reverse=True)]

    return jsonify({
        "name": course.name,
        "courseKey": course.course_key,
        "mapIcon": course.map_icon,
        "summary": summary,
        "currentMachineWrs": currentMachineWrs,
        "history": history,
        "stats": {
            "byPlayer": stats_by_player,
            "byMachine": stats_by_machine,
            "byNation": stats_by_nation,
        }
    })
