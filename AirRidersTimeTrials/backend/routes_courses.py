# routes_courses.py
from datetime import date
from flask import Blueprint, jsonify
from extensions import db
from models import Course, Record, User

bp_courses = Blueprint("course", __name__)

def days_since(d: date) -> int:
    if not d:
        return 0
    return max((date.today() - d).days, 0)

@bp_courses.get("/api/course/<course_key>")
def get_course(course_key):
    course = Course.query.filter_by(course_key=course_key).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # ----------------------------
    # Current Machine WRs:
    # best time per machine for this course (lowest time_ms)
    # ----------------------------
    best_per_machine = (
        db.session.query(
            Record.machine_id,
            db.func.min(Record.time_ms).label("best_ms")
        )
        .filter(Record.course_id == course.id)
        .group_by(Record.machine_id)
        .subquery()
    )

    current_recs = (
        db.session.query(Record)
        .join(
            best_per_machine,
            db.and_(
                Record.machine_id == best_per_machine.c.machine_id,
                Record.time_ms == best_per_machine.c.best_ms,
                Record.course_id == course.id
            )
        )
        .order_by(Record.machine_id.asc())
        .all()
    )

    currentMachineWrs = []
    for r in current_recs:
        nation_code = (r.user.country_code or "").lower()
        currentMachineWrs.append({
            "machineName": r.machine.name,
            "machineIcon": f"static/{r.machine.icon}".replace("\\", "/") if not r.machine.icon.startswith("static/") else r.machine.icon,
            "date": r.date_set.isoformat() if r.date_set else "",
            "time": r.time_str,
            "player": r.user.username,
            "nationCode": nation_code,  # expects lowercase for svg file names
            "days": days_since(r.date_set),
            "lap1": r.lap1,
            "lap2": r.lap2,
            "lap3": r.lap3,
            "charIcon": f"static/{r.character.icon}".replace("\\", "/") if not r.character.icon.startswith("static/") else r.character.icon,
            "charAlt": r.character.name
        })

    # ----------------------------
    # History (optional but matches your UI)
    # newest first
    # ----------------------------
    history_q = (
        Record.query
        .filter(Record.course_id == course.id)
        .order_by(Record.date_set.desc(), Record.time_ms.asc())
        .limit(200)
        .all()
    )

    history = []
    for r in history_q:
        nation_code = (r.user.country_code or "").lower()
        history.append({
            "date": r.date_set.isoformat() if r.date_set else "",
            "machineName": r.machine.name,
            "machineIcon": f"static/{r.machine.icon}".replace("\\", "/") if not r.machine.icon.startswith("static/") else r.machine.icon,
            "time": r.time_str,
            "player": r.user.username,
            "nationCode": nation_code,
            "days": days_since(r.date_set),
            "lap1": r.lap1,
            "lap2": r.lap2,
            "lap3": r.lap3,
            "charIcon": f"static/{r.character.icon}".replace("\\", "/") if not r.character.icon.startswith("static/") else r.character.icon
        })

    # ----------------------------
    # Course Stats (based on current machine WRs)
    # ----------------------------
    total_days = sum(x["days"] for x in currentMachineWrs) or 1  # avoid divide-by-zero

    # By Player
    by_player = {}
    for x in currentMachineWrs:
        by_player.setdefault(x["player"], 0)
        by_player[x["player"]] += x["days"]
    statsByPlayer = [
        {"player": p, "total": d, "pct": round((d / total_days) * 100, 2)}
        for p, d in sorted(by_player.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # By Machine
    by_machine = {}
    for x in currentMachineWrs:
        by_machine.setdefault(x["machineName"], 0)
        by_machine[x["machineName"]] += x["days"]
    statsByMachine = [
        {"machine": m, "total": d, "pct": round((d / total_days) * 100, 2)}
        for m, d in sorted(by_machine.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # By Nation (count of current WRs per nation)
    by_nation = {}
    for x in currentMachineWrs:
        code = x["nationCode"] or "??"
        by_nation.setdefault(code, 0)
        by_nation[code] += 1
    statsByNation = [
        {"nation": n, "count": c}
        for n, c in sorted(by_nation.items(), key=lambda kv: kv[1], reverse=True)
    ]

    summary = {
        "totalMachineWrs": len(currentMachineWrs),
        "uniquePlayers": len(set(x["player"] for x in currentMachineWrs)),
        "uniqueNations": len(set(x["nationCode"] for x in currentMachineWrs if x["nationCode"])),
        "uniqueMachines": len(set(x["machineName"] for x in currentMachineWrs)),
    }

    # map icon path (your Course.map_icon already looks like images/mapICONS/Name.png)
    map_icon = ""
    if course.map_icon:
        map_icon = course.map_icon.replace("\\", "/")
        if not map_icon.startswith("static/"):
            map_icon = f"static/{map_icon}"

    return jsonify({
        "key": course.course_key,
        "name": course.name,
        "mapIcon": map_icon,
        "currentMachineWrs": currentMachineWrs,
        "history": history,
        "summary": summary,
        "stats": {
            "byPlayer": statsByPlayer,
            "byMachine": statsByMachine,
            "byNation": statsByNation
        }
    })
