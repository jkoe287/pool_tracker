from flask import Flask, request, render_template, redirect, jsonify
import sqlite3
import datetime
import json
from scripts import helpers

app = Flask(__name__)

# for future, have range for values

"""ph REAL CHECK (ph BETWEEN 6.0 AND 8.5),
            fac REAL CHECK (fac >= 0),
            tac REAL CHECK (tac >= 0),
            tds REAL CHECK (tds >= 0),"""

# set up database
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)

    
    c.execute("""
        CREATE TABLE IF NOT EXISTS water_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pool_id INTEGER NOT NULL,

            test_date DATE NOT NULL,
            test_time TIME NOT NULL,
            test_slot INTEGER NOT NULL,

            bather_load INTEGER,
              
            temp REAL,
            tds REAL, 
              
            ph REAL,
            fac REAL,
            tac REAL,
              
            an_ph REAL,
            an_fac REAL,

            tester TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (pool_id, test_date, test_slot)
              
        );
    """)

    
    c.execute("""
        INSERT OR IGNORE INTO pools (name)
        VALUES ('Main'), ('Spa');
    """)


    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("data.db")

init_db()


@app.route("/")
def form():
    day_number = datetime.date.today().weekday()

    mp_water_tests = helpers.open_json('schedule.json')['pool_tests']['main_pool_tests'][day_number]
    sp_water_tests = helpers.open_json('schedule.json')['pool_tests']['spa_tests'][day_number]

    water_tests = [mp_water_tests, sp_water_tests]

    return render_template("new_form.html", water_tests = water_tests, weekday = day_number)

@app.route("/schedule")
def schedule():
    return helpers.open_json('schedule.json')

@app.route("/api/water-test", methods=["POST"])
def save_water_test():
    data = request.json

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO water_tests (
            pool_id, test_date, test_time, test_slot,
            bather_load, temp, tds, ph, fac, tac, 
            an_ph, an_fac, tester
        )
        VALUES (
            (SELECT id FROM pools WHERE name=?),
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """
    , (
        data["pool"].capitalize(),
        datetime.date.today(),
        data["time"],
        data['slot'],

        data["bather_load"],
        data["temp"],
        data["tds"],
        data["ph"],
        data["fac"],
        data["tac"],

        data["an_ph"],
        data["an_fac"],
        data["tester"]
    ))

    db.commit()
    db.close()

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)


