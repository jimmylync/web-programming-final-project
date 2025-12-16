from datetime import date, datetime, timedelta
from collections import defaultdict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_

from extensions import db
from models import Course, Machine, Character, User, Record

bp_stats = Blueprint("stats", __name__, url_prefix="/api")


# ---------- helpers ----------
def days_since(d: date) -> int:
    if not d:
        return 0
    return (date.today() - d).days


def static_path(p: str) -> str:
    """
    Your DB stores paths like: "images/mapICONS/Floria_Fields.png"
    Frontend expects: "static/images/..."
    """
    if not p:
        return ""
    p = p.replace("\\", "/").lstrip("/")
    if p.startswith("static/"):
        return p
    return f"static/{p}"


def record_to_course_machine_row(r: Record):
    return {
        "course_key": r.course.course_key,
        "course_name": r.course.name,
        "machine_name": r.machine.name,
        "machine_icon": static_path(r.machine.icon),
        "time": r.time_str,
        "player": r.user.username,
        "nation_code": (r.user.country_code or "us").lower(),
        "date": r.date_set.isoformat() if r.date_set else None,
        "days": days_since(r.date_set),
        "character_name": r.character.name,
        "char_icon": static_path(r.character.icon),
    }


# ---------- core: find CURRENT WR per (course, machine) ----------
def get_current_wr_by_course_machine():
    """
    Returns dict keyed by (course_id, machine_id) -> Record
    """
    # 1) min time_ms per course+machine
    sub = (
        db.session.query(
            Record.course_id.label("course_id"),
            Record.machine_id.label("machine_id"),
            func.min(Record.time_ms).label("best_ms"),
        )
        .group_by(Record.course_id, Record.machine_id)
        .subquery()
    )

    # 2) join back to records; if ties, take earliest date_set then earliest created_at
    rows = (
        db.session.query(Record)
        .join(
            sub,
            and_(
                Record.course_id == sub.c.course_id,
                Record.machine_id == sub.c.machine_id,
                Record.time_ms == sub.c.best_ms,
            ),
        )
        .order_by(Record.course_id, Record.machine_id, Record.date_set.asc(), Record.created_at.asc())
        .all()
    )

    # 3) pick first per key (handles ties)
    best = {}
    for r in rows:
        key = (r.course_id, r.machine_id)
        if key not in best:
            best[key] = r
    return best


# ---------- core: compute WR HOLD DURATIONS properly ----------
def compute_wr_days_by_user():
    """
    For each (course, machine), walk records in chronological order
    and count "days held" whenever a record becomes the new best.
    This yields total WR days per user (real timeline-based).
    """
    totals = defaultdict(int)       # user_id -> total days
    wr_counts = defaultdict(int)    # user_id -> number of WRs achieved (events)
    wr_pairs = defaultdict(set)     # user_id -> set of (course_id,machine_id) where they held WR at least once

    # load all records ordered by (course, machine, date_set, created_at)
    all_recs = (
        db.session.query(Record)
        .join(Record.course)
        .join(Record.machine)
        .join(Record.user)
        .join(Record.character)
        .order_by(Record.course_id, Record.machine_id, Record.date_set.asc(), Record.created_at.asc())
        .all()
    )

    # group by (course_id, machine_id)
    grouped = defaultdict(list)
    for r in all_recs:
        grouped[(r.course_id, r.machine_id)].append(r)

    for pair, recs in grouped.items():
        best_ms = None
        current_holder = None
        current_start = None  # date

        for r in recs:
            # first record becomes the WR
            if best_ms is None:
                best_ms = r.time_ms
                current_holder = r.user_id
                current_start = r.date_set
                wr_counts[current_holder] += 1
                wr_pairs[current_holder].add(pair)
                continue

            # WR improves ONLY if time_ms is smaller
            if r.time_ms < best_ms:
                # close out previous holder duration
                end_date = r.date_set
                if current_holder is not None and current_start is not None and end_date is not None:
                    duration = (end_date - current_start).days
                    if duration > 0:
                        totals[current_holder] += duration

                # new WR starts
                best_ms = r.time_ms
                current_holder = r.user_id
                current_start = r.date_set
                wr_counts[current_holder] += 1
                wr_pairs[current_holder].add(pair)

        # close out last holder until today
        if current_holder is not None and current_start is not None:
            duration = (date.today() - current_start).days
            if duration > 0:
                totals[current_holder] += duration

    return totals, wr_counts, wr_pairs


# =========================
#   /api/current-wrs
#   best time per COURSE
# =========================
@bp_stats.get("/current-wrs")
def current_wrs():
    # min time_ms per course (across machines)
    sub = (
        db.session.query(
            Record.course_id.label("course_id"),
            func.min(Record.time_ms).label("best_ms"),
        )
        .group_by(Record.course_id)
        .subquery()
    )

    rows = (
        db.session.query(Record)
        .join(sub, and_(Record.course_id == sub.c.course_id, Record.time_ms == sub.c.best_ms))
        .join(Record.course)
        .join(Record.machine)
        .join(Record.character)
        .join(Record.user)
        .order_by(Record.course_id, Record.date_set.asc(), Record.created_at.asc())
        .all()
    )

    # pick one per course (ties)
    best_by_course = {}
    for r in rows:
        if r.course_id not in best_by_course:
            best_by_course[r.course_id] = r

    out = [record_to_course_machine_row(r) for r in best_by_course.values()]
    # keep stable ordering by course name
    out.sort(key=lambda x: x["course_name"].lower())
    return jsonify(out)


# =========================
#   /api/wr-snapshot
#   best time per (COURSE, MACHINE)
# =========================
@bp_stats.get("/wr-snapshot")
def wr_snapshot():
    current = get_current_wr_by_course_machine()
    rows = [record_to_course_machine_row(r) for r in current.values()]

    # sort by course then machine
    rows.sort(key=lambda x: (x["course_name"].lower(), x["machine_name"].lower()))
    return jsonify(rows)


# =========================
#   /api/recent-wrs?days=5
#   current WRs set within last N days
# =========================
@bp_stats.get("/recent-wrs")
def recent_wrs():
    days = int(request.args.get("days", 5))
    cutoff = date.today() - timedelta(days=days)

    current = get_current_wr_by_course_machine()
    rows = []
    for r in current.values():
        if r.date_set and r.date_set >= cutoff:
            rows.append(record_to_course_machine_row(r))

    rows.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(rows)


# =========================
#   /api/rankings/players
#   rank by WR count + total WR days
# =========================
@bp_stats.get("/rankings/players")
def player_rankings():
    totals_days, wr_counts, _ = compute_wr_days_by_user()

    users = db.session.query(User).all()
    rows = []
    for u in users:
        rows.append({
            "player": u.username,
            "nation_code": (u.country_code or "us").lower(),
            "wr_count": int(wr_counts.get(u.id, 0)),
            "total_wr_days": int(totals_days.get(u.id, 0)),
        })

    # sort: WR count desc, then WR days desc, then name
    rows.sort(key=lambda r: (-r["wr_count"], -r["total_wr_days"], r["player"].lower()))

    # assign ranks (1..n)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    return jsonify(rows)


# =========================
#   /api/rankings/countries
#   rank by total WR count + unique players
# =========================
@bp_stats.get("/rankings/countries")
def country_rankings():
    current = get_current_wr_by_course_machine().values()

    wr_count_by_country = defaultdict(int)
    players_by_country = defaultdict(set)

    for r in current:
        code = (r.user.country_code or "us").lower()
        wr_count_by_country[code] += 1
        players_by_country[code].add(r.user_id)

    rows = []
    for code, count in wr_count_by_country.items():
        rows.append({
            "nation_code": code,
            "wr_count": int(count),
            "unique_players": int(len(players_by_country.get(code, set()))),
        })

    # sort: WR count desc, then unique players desc, then code
    rows.sort(key=lambda r: (-r["wr_count"], -r["unique_players"], r["nation_code"]))

    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    return jsonify(rows)
