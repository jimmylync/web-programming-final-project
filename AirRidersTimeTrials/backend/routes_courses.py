from flask import Blueprint, jsonify
from extensions import db
from models import Course, Machine, Character, Record, User

bp_courses = Blueprint("courses", __name__)

@bp_courses.get("/api/course/<course_key>")
def get_course(course_key):
    course = Course.query.filter_by(course_key=course_key).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # current WR per machine = lowest time_ms for that course + machine
    machines = Machine.query.order_by(Machine.name.asc()).all()
    current_machine_wrs = []

    for m in machines:
        wr = (
            Record.query
            .filter_by(course_id=course.id, machine_id=m.id)
            .order_by(Record.time_ms.asc(), Record.date_set.desc())
            .first()
        )
        if wr:
            current_machine_wrs.append({
                "machineName": wr.machine.name,
                "machineIcon": wr.machine.icon,
                "date": wr.date_set.isoformat(),
                "time": wr.time_str,
                "player": wr.user.username,
                "nationCode": (wr.user.country_code or "us"),
                "days": 0,  # optional, compute later if you want
                "lap1": wr.lap1,
                "lap2": wr.lap2,
                "lap3": wr.lap3,
                "charIcon": wr.character.icon,
                "charAlt": wr.character.name
            })

    # history: latest 50 records for this course
    history = (
        Record.query
        .filter_by(course_id=course.id)
        .order_by(Record.date_set.desc(), Record.time_ms.asc())
        .limit(50)
        .all()
    )

    history_rows = [{
        "date": r.date_set.isoformat(),
        "machineName": r.machine.name,
        "machineIcon": r.machine.icon,
        "time": r.time_str,
        "player": r.user.username,
        "nationCode": (r.user.country_code or "us"),
        "days": 0,
        "lap1": r.lap1,
        "lap2": r.lap2,
        "lap3": r.lap3,
        "charIcon": r.character.icon,
        "charAlt": r.character.name
    } for r in history]

    # very basic summary (you can improve later)
    unique_players = db.session.query(User.id).join(Record, Record.user_id == User.id).filter(Record.course_id == course.id).distinct().count()
    unique_nations = db.session.query(User.country_code).join(Record, Record.user_id == User.id).filter(Record.course_id == course.id).distinct().count()
    total_wrs = len(current_machine_wrs)

    return jsonify({
        "name": course.name,
        "mapIcon": course.map_icon,
        "summary": {
            "totalMachineWrs": total_wrs,
            "uniquePlayers": unique_players,
            "uniqueNations": unique_nations,
            "uniqueMachines": total_wrs
        },
        "currentMachineWrs": current_machine_wrs,
        "statsByPlayer": [],
        "statsByMachine": [],
        "statsByNation": [],
        "history": history_rows
    })
