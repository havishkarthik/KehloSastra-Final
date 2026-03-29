import os
import sqlite3
from datetime import datetime, date

from flask import Flask, jsonify, request, render_template, g

app = Flask(__name__)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "bookings.db"),
)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                sport      TEXT    NOT NULL,
                date       TEXT    NOT NULL,
                start_time TEXT    NOT NULL,
                end_time   TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        db.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/book", methods=["POST"])
def book():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    sport = (data.get("sport") or "").strip()
    booking_date = (data.get("date") or "").strip()
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()

    # --- Basic validation ---
    if not all([name, sport, booking_date, start_time, end_time]):
        return jsonify({"success": False, "error": "All fields are required."}), 400

    try:
        booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if booking_date_obj < date.today():
        return jsonify({"success": False, "error": "Cannot book a slot in the past."}), 400

    try:
        start_dt = datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{booking_date} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"success": False, "error": "Invalid time format. Use HH:MM."}), 400

    if end_dt <= start_dt:
        return jsonify({"success": False, "error": "End time must be after start time."}), 400

    if booking_date_obj == date.today() and start_dt <= datetime.now():
        return jsonify({"success": False, "error": "Cannot book a slot that has already started."}), 400

    db = get_db()

    # --- Anti-overlap check ---
    overlapping = db.execute(
        """
        SELECT id FROM bookings
        WHERE sport = ?
          AND date  = ?
          AND start_time < ?
          AND end_time   > ?
        """,
        (sport, booking_date, end_time, start_time),
    ).fetchone()

    if overlapping:
        return jsonify(
            {"success": False, "error": "This slot overlaps with an existing booking. Please choose a different time."}
        ), 409

    db.execute(
        """
        INSERT INTO bookings (name, sport, date, start_time, end_time, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """,
        (name, sport, booking_date, start_time, end_time),
    )
    db.commit()

    return jsonify({"success": True, "message": "Booking confirmed successfully!"}), 201


@app.route("/bookings", methods=["GET"])
def get_bookings():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM bookings ORDER BY date, start_time"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/availability", methods=["GET"])
def availability():
    sport = request.args.get("sport", "").strip()
    booking_date = request.args.get("date", "").strip()

    if not sport or not booking_date:
        return jsonify({"error": "sport and date query parameters are required."}), 400

    db = get_db()
    rows = db.execute(
        """
        SELECT id, name, start_time, end_time
        FROM bookings
        WHERE sport = ? AND date = ?
        ORDER BY start_time
        """,
        (sport, booking_date),
    ).fetchall()

    return jsonify({"sport": sport, "date": booking_date, "bookings": [dict(r) for r in rows]})


@app.route("/admin/bookings", methods=["GET"])
def admin_bookings():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM bookings ORDER BY date, sport, start_time"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
