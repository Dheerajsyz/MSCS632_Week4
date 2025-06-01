"""
app.py

Flask app that serves a Bootstrap UI for entering employees and their
shift preferences. Uses scheduler.generate_schedule to produce the final schedule.
"""

import json
from flask import Flask, render_template, request, jsonify
from scheduler import generate_schedule, DAYS_OF_WEEK, VALID_SHIFTS

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    """
    Render the main UI (templates/index.html).
    """
    return render_template("index.html", days=DAYS_OF_WEEK, shifts=VALID_SHIFTS)


@app.route("/schedule", methods=["POST"])
def create_schedule():
    """
    Handle schedule generation request.
    """
    try:
        if request.is_json:
            data = request.get_json()
            employees = data.get('employees', [])
        else:
            # fallback for form POSTs (shouldn't happen with new UI)
            employees = []
        if not employees or not isinstance(employees, list):
            return render_template('index.html', error='No employees provided.', days=DAYS_OF_WEEK, shifts=VALID_SHIFTS)
        # Convert frontend structure to backend expected format
        raw_preferences = {}
        for emp in employees:
            name = emp.get('name', '').strip()
            prefs = emp.get('preferences', {})
            if not name or not isinstance(prefs, dict):
                continue
            # Convert [first, second] to {shift: priority, ...} for each day
            day_map = {}
            for day in DAYS_OF_WEEK:
                shifts = prefs.get(day, [None, None])
                pri_map = {}
                used = set()
                rank = 1
                for s in shifts:
                    if s and s != 'none' and s not in used and s in VALID_SHIFTS:
                        pri_map[s] = rank
                        used.add(s)
                        rank += 1
                day_map[day] = pri_map if pri_map else None
            raw_preferences[name] = day_map
        # Generate schedule
        schedule = generate_schedule(raw_preferences)
        return render_template('index.html', schedule=schedule, days=DAYS_OF_WEEK, shifts=VALID_SHIFTS)
    except Exception as e:
        # Try to preserve the employee list on error
        employees = []
        try:
            if request.is_json:
                data = request.get_json()
                employees = data.get('employees', [])
        except Exception:
            pass
        return render_template('index.html', error=str(e), days=DAYS_OF_WEEK, shifts=VALID_SHIFTS, employees=employees)


if __name__ == "__main__":
    # In production, set debug=False
    app.run(host="0.0.0.0", port=8080, debug=True)
