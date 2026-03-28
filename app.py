from flask import Flask, request, render_template, redirect, jsonify
import sqlite3
import datetime
import json
from scripts import helpers

app = Flask(__name__)

# -------------------------
# DATABASE SETUP
# -------------------------
def init_db():
    conn = sqlite3.connect("full_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            time_slot INTEGER
            temp REAL,
            bath_l INTEGER,
            ph REAL,
            fac REAL,
            tac REAL,
            tds REAL,
            an_ph REAL,
            an_fac REAL,
            tester TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# ROUTES
# -------------------------

# Entry page
@app.route("/")
def form():
    return render_template("form.html")

@app.route("/test")
def new_form():

    day_number = datetime.date.today().weekday()
    water_tests = helpers.open_json('schedule.json')['main_pool_tests'][day_number]
    
    return render_template("new_form.html", rows = water_tests, weekday = day_number)

# Handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    ph = request.form["ph"]
    fac = request.form["fac"]
    bather = request.form["bather"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (timestamp, ph, fac, bather_load) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), ph, fac, bather)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# Return pool testing schedule as JSON
@app.route("/schedule")
def schedule():
    return helpers.open_json('schedule.json')
    

# Return data as JSON (for graphs)
@app.route("/data")
def data():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, ph, fac FROM logs")
    rows = c.fetchall()
    conn.close()

    return jsonify(rows)

# Graph page
@app.route("/graph")
def graph():
    return render_template("graph.html")

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


