from flask import Flask, request, render_template, redirect, jsonify
import sqlite3
import datetime
sqlite3.register_adapter(datetime.date, lambda d: d.isoformat())
sqlite3.register_converter("DATE", lambda s: s.decode())
import json
from scripts import helpers
from collections import OrderedDict

app = Flask(__name__)

def get_tests_for_pool(pool_names, day):
    db = get_db()
    cursor = db.cursor()

    pool_tests = []
    for index, pool_name  in enumerate(pool_names):
        cursor.execute("""
            SELECT wt.*, p.name AS pool_name
            FROM water_tests wt
            JOIN pools p ON p.id = wt.pool_id
            WHERE p.name = ?
            AND wt.test_date = ?
            ORDER BY wt.test_slot
        """, (pool_name, day))
        
        rows = cursor.fetchall()
        pool_tests.append([dict(r) for r in rows])

    db.close()
    return pool_tests

def merge_schedule_with_tests(full_schedule, db_tests):
    merged = []

    for pool_index, pool_schedule in enumerate(full_schedule):
        pool_rows = []

        # Build lookup for this pool: time → db_row
        lookup = {t["test_time"]: t for t in db_tests[pool_index]}

        for slot in pool_schedule:
            time = slot["time"]

            if time in lookup:
                db_row = lookup[time]

                # Keep only keys that exist in the schedule slot
                filtered = {
                    key: db_row.get(key, slot[key])
                    for key in slot.keys()
                }

                pool_rows.append(filtered)
            else:
                pool_rows.append(slot)

        merged.append(pool_rows)

    return merged


# for future, have range for values

"""ph REAL CHECK (ph BETWEEN 6.0 AND 8.5),
            fac REAL CHECK (fac >= 0),
            tac REAL CHECK (tac >= 0),
            tds REAL CHECK (tds >= 0),"""

# set up database
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")
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

            temp REAL,
            bather_load INTEGER,
            ph REAL,
            fac REAL,
            tac REAL,
            tds REAL, 

            an_ph REAL,
            an_fac REAL,

            tester TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (pool_id, test_date, test_slot),

            FOREIGN KEY (pool_id) REFERENCES pools(id)
        );
    """)

    
    c.execute("""
        INSERT OR IGNORE INTO pools (name)
        VALUES ('main'), ('spa');
    """)


    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

init_db()


@app.route("/")
def form():

    day = datetime.date.today()
    
    day_number = day.weekday()

    pool_info = helpers.open_json('pool_info.json')

    pool_names = list(pool_info['pool_tests'].keys())

    pool_test_schedules = [pool_info['pool_tests'][name][day_number] for name in pool_names]
  
    # find pool headers
    pool_header_labels = [
        list(OrderedDict.fromkeys(
            pool_info['variable_info'][k]['html_label']
            for test in pool_test_s
            for k, v in test.items()
            if v is True
        ))
        for pool_test_s in pool_test_schedules
    ]

    # find completed tests for said day from sql database
    completed_tests = get_tests_for_pool(pool_names, day)

    pool_test_data = merge_schedule_with_tests(pool_test_schedules, completed_tests)
    
    print(pool_test_data)

    return render_template("new_form.html", 
                           pool_info = pool_info,
                           pool_names = pool_names,
                           pool_test_data = pool_test_data,
                           pool_header_labels = pool_header_labels,
                           day_date = day.strftime("%d-%m-%Y"),
                           day_weekday = day.strftime("%A")
                           )

@app.route("/pool_info")
def schedule():
    return helpers.open_json('pool_info.json')

@app.route("/api/water-test", methods=["POST"])
def save_water_test():
    data = request.json
    print(data)
    
    with get_db() as db:
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO water_tests (
                pool_id, test_date, test_time, test_slot,
                temp, bather_load, ph, fac, tac, tds,
                an_ph, an_fac, tester
            )
            VALUES (
                (SELECT id FROM pools WHERE name=?),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            data["pool"],
            datetime.date.today(),
            data["time"],
            data['slot'],

            data["temp"],
            data["bather_load"],
            data["ph"],
            data["fac"],
            data["tac"],
            data["tds"],

            data["an_ph"],
            data["an_fac"],
            data["tester"]
        ))

    
    return jsonify({
            "status": "ok",
            "message": "Water test saved"
        }), 200


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)


