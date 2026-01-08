from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import hashlib
import os
import shutil
from datetime import datetime
from functools import wraps
from datetime import datetime
import pytz
def format_ist_time(ts):
    """
    Converts DB timestamp to IST & Indian readable format
    """
    ist = pytz.timezone("Asia/Kolkata")

    # if ts is string like '2025-12-29 09:57:05'
    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

    # assume DB time is UTC
    dt = pytz.UTC.localize(dt).astimezone(ist)

    return dt.strftime("%d %b %Y • %I:%M %p")


def backup_database():
    if not os.path.exists("backups"):
        os.makedirs("backups")

    today = datetime.now().strftime("%Y_%m_%d")
    backup_file = f"backups/backup_{today}.db"

    if not os.path.exists(backup_file):
        shutil.copy("database.db", backup_file)


app = Flask(__name__)
import os
app.secret_key = os.urandom(24)


from datetime import timedelta

app.permanent_session_lifetime = timedelta(minutes=30)


def get_db():
    return sqlite3.connect("database.db")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                return "Unauthorized Access", 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def init_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'COMPOUNDER'
        )
    """)
    conn.commit()
    conn.close()

def create_admin():
    conn = get_db()
    cursor = conn.cursor()

    password = "vikas"  # CHANGE THIS
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", password_hash)
        )
        conn.commit()
    except:
        pass

    conn.close()

def init_contacts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()
def init_patients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            contact_id INTEGER
        )
    """)
    conn.commit()
    conn.close()
def init_visits():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            symptoms TEXT,
            diagnosis TEXT,
            advice TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_address_column():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE patients ADD COLUMN address TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.close()

def add_payment_columns():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN fee INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE visits ADD COLUMN paid INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE visits ADD COLUMN credit INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def add_payment_mode_column():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN payment_mode TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def add_audit_columns():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN is_void INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE visits ADD COLUMN void_reason TEXT")
        cursor.execute("ALTER TABLE visits ADD COLUMN voided_by TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def add_edit_columns():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN edited INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE visits ADD COLUMN edit_reason TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()
def add_void_column():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "ALTER TABLE visits ADD COLUMN is_void INTEGER DEFAULT 0"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()




init_users()
#create_admin()          # run once, then COMMENT this line
init_contacts()
init_patients()
init_visits()
add_audit_columns()
add_address_column()
backup_database()
add_payment_columns()
add_payment_mode_column()
add_edit_columns()
add_void_column()





@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[3]   # 👈 role column
            session.permanent = True
            return redirect("/")

        else:
            return "Invalid login"

    return render_template("login.html")

from functools import wraps



def is_valid_mobile(mobile):
    return re.fullmatch(r"\d{10}", mobile)

def is_valid_name(name):
    return re.fullmatch(r"[A-Za-z ]+", name)

def is_valid_age(age):
    return age.isdigit() and 0 <= int(age) <= 120






@app.route("/")
@login_required
def home():
    return render_template("home.html")

from flask import redirect, url_for

@app.route("/add_patient", methods=["POST"])
@login_required
def add_patient():
    name = request.form["name"].strip()
    age = request.form["age"].strip()
    gender = request.form["gender"]
    mobile = request.form["mobile"].strip()
    address = request.form["address"].strip()


    # BACKEND VALIDATION
    if not is_valid_name(name):
        return "Invalid name. Only letters allowed."

    if not is_valid_age(age):
        return "Invalid age."

    if gender not in ["M", "F", "O"]:
        return "Invalid gender selection."

    if not is_valid_mobile(mobile):
        return "Invalid mobile number."
    if not address:
        return "Address is required."



    conn = get_db()
    cursor = conn.cursor()

    # 1. Get or create contact
    cursor.execute("SELECT id FROM contacts WHERE mobile=?", (mobile,))
    contact = cursor.fetchone()

    if contact:
        contact_id = contact[0]
    else:
        cursor.execute("INSERT INTO contacts (mobile) VALUES (?)", (mobile,))
        conn.commit()
        contact_id = cursor.lastrowid

    # 2. Check for similar patient (same name under same contact)
    cursor.execute(
        "SELECT * FROM patients WHERE contact_id=? AND LOWER(name)=?",
        (contact_id, name)
    )
    existing_patient = cursor.fetchone()

    if existing_patient:
        conn.close()
        return render_template(
            "confirm_patient.html",
            patient=existing_patient,
            name=request.form["name"],
            age=age,
            gender=gender,
            address=address,
            contact_id=contact_id
        )

    # 3. No duplicate → insert directly
    cursor.execute(
        "INSERT INTO patients (name, age, gender, address, contact_id) VALUES (?, ?, ?, ?, ?)",
        (request.form["name"], age, gender, address, contact_id)
    )
    conn.commit()

    patient_id = cursor.lastrowid
    conn.close()

    return redirect(url_for("add_visit_page", patient_id=patient_id))


@app.route("/add_visit/<int:patient_id>")
@login_required
def add_visit_page(patient_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = cursor.fetchone()

    # ✅ Correct running credit
    cursor.execute("""
    SELECT COALESCE(SUM(
        CASE
            WHEN symptoms = 'PAYMENT' THEN -paid
            ELSE fee - paid
        END
    ), 0)
    FROM visits
    WHERE patient_id = ?
      AND is_void = 0
""", (patient_id,))
    pending_credit = cursor.fetchone()[0]

# Never show negative pending
    pending_credit = max(pending_credit, 0)



    conn.close()

    return render_template(
        "add_visit.html",
        patient=patient,
        pending_credit=pending_credit
    )


@app.route("/add_visit", methods=["POST"])
@login_required
def save_visit():
    data = request.form

    patient_id = int(data["patient_id"])
    fee = int(data["fee"])
    paid = int(data["paid"])

    conn = get_db()
    cursor = conn.cursor()

    # 🔐 FETCH EXISTING PENDING BEFORE THIS VISIT
    cursor.execute("""
        SELECT COALESCE(SUM(fee),0) - COALESCE(SUM(paid),0)
        FROM visits
        WHERE patient_id = ?
    """, (patient_id,))
    pending_before = cursor.fetchone()[0]

    # ✅ MAX ALLOWED PAYMENT = today's fee + previous pending
    max_allowed_payment = fee + pending_before

    if paid > max_allowed_payment:
        conn.close()
        return f"Payment exceeds total pending amount (₹{max_allowed_payment})"

    # ✅ SAFE CREDIT CALCULATION
    credit = fee - paid

    payment_mode = request.form.get("payment_mode")
    if paid == 0:
        payment_mode = None

    # ✅ INSERT VISIT
    cursor.execute("""
        INSERT INTO visits
        (patient_id, symptoms, diagnosis, advice, fee, paid, credit, payment_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        data["symptoms"],
        data["diagnosis"],
        data["advice"],
        fee,
        paid,
        credit,
        payment_mode
    ))

    conn.commit()
    conn.close()

    return render_template(
        "visit_saved.html",
        patient_id=patient_id
    )

@app.route("/edit_visit/<int:visit_id>", methods=["GET", "POST"])
@login_required
def edit_visit(visit_id):

    if session.get("role") not in ["ADMIN", "DOCTOR"]:
        return "Unauthorized", 403

    conn = get_db()
    cursor = conn.cursor()

    # Fetch visit
    cursor.execute("""
        SELECT id, patient_id, symptoms, diagnosis, advice, fee, paid, payment_mode
        FROM visits
        WHERE id=?
    """, (visit_id,))
    visit = cursor.fetchone()

    if not visit:
        conn.close()
        return "Visit not found"

    patient_id = visit[1]
    is_payment = (visit[2] == "PAYMENT")

    if request.method == "POST":
        fee = int(request.form.get("fee", 0))
        paid = int(request.form.get("paid", 0))
        payment_mode = request.form.get("payment_mode")
        diagnosis = request.form.get("diagnosis")
        advice = request.form.get("advice")
        reason = request.form.get("reason")

        # ✅ Pending BEFORE this visit (exclude this visit)
        cursor.execute("""
            SELECT COALESCE(SUM(fee),0) - COALESCE(SUM(paid),0)
            FROM visits
            WHERE patient_id = ?
              AND id != ?
        """, (patient_id, visit_id))
        pending_before = cursor.fetchone()[0]

        max_allowed_payment = pending_before + fee

        if paid > max_allowed_payment:
            conn.close()
            return f"Payment exceeds total pending amount (₹{max_allowed_payment})"

        if paid == 0:
            payment_mode = None

        cursor.execute("""
            UPDATE visits
            SET fee=?, paid=?, payment_mode=?,
                diagnosis=?, advice=?,
                edited=1, edit_reason=?
            WHERE id=?
        """, (
            fee, paid, payment_mode,
            diagnosis, advice,
            reason, visit_id
        ))

        conn.commit()
        conn.close()
        return redirect(f"/history/{patient_id}")

    conn.close()
    return render_template(
        "edit_visit.html",
        visit=visit,
        is_payment=is_payment
    )


@app.route("/history/<int:patient_id>")
@login_required
def history(patient_id):
    conn = get_db()
    cursor = conn.cursor()

    # Patient info
    cursor.execute("""
        SELECT patients.id, patients.name, patients.age, patients.gender,
               patients.address, contacts.mobile
        FROM patients
        JOIN contacts ON patients.contact_id = contacts.id
        WHERE patients.id=?
    """, (patient_id,))
    patient = cursor.fetchone()

    # ALL visits (OPD + PAYMENT), chronological
    cursor.execute("""
        SELECT id, date, symptoms, diagnosis, advice,
               fee, paid, payment_mode
        FROM visits
        WHERE patient_id=?
        ORDER BY date ASC
    """, (patient_id,))
    rows = cursor.fetchall()

    visits = []
    running_balance = 0

    for r in rows:
        fee = r[5] or 0
        paid = r[6] or 0

        running_balance += (fee - paid)

        dt = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
        dt = dt + timedelta(hours=5, minutes=30)

        visits.append({
            "id": r[0],
            "date": dt.strftime("%d %b %Y • %I:%M %p"),
            "symptoms": r[2],
            "diagnosis": r[3],
            "advice": r[4],
            "fee": fee,
            "paid": paid,
            "credit": running_balance,   # 🔑 REQUIRED BY TEMPLATE
            "payment_mode": r[7],
            "is_payment": r[2] == "PAYMENT"
        })

    conn.close()

    return render_template(
        "history.html",
        patient=patient,
        visits=list(reversed(visits)),
        total_udhaar=running_balance
    )



@app.route("/add_payment/<int:patient_id>", methods=["GET", "POST"])
@login_required
def add_payment(patient_id):
    conn = get_db()
    cursor = conn.cursor()

    # patient info
    cursor.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = cursor.fetchone()

    # pending credit (running balance)
    cursor.execute("""
        SELECT COALESCE(SUM(fee),0) - COALESCE(SUM(paid),0)
        FROM visits
        WHERE patient_id=?
        AND is_void = 0
    """, (patient_id,)) #idhr bhi add kara
    pending_credit = cursor.fetchone()[0]

    # ✅ ONLY INSERT WHEN FORM IS SUBMITTED
    if request.method == "POST":
        paid = int(request.form["paid"])
        remark = request.form.get("remark", "Payment received")
        payment_mode = request.form["payment_mode"]

        cursor.execute("""
            INSERT INTO visits
            (patient_id, symptoms, diagnosis, advice, fee, paid, credit, payment_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            "PAYMENT",
            "PAYMENT ONLY",
            remark,
            0,
            paid,
            -paid,          # 👈 reduces udhaar
            payment_mode
        ))

        conn.commit()
        conn.close()
        return redirect(f"/history/{patient_id}")

    # ✅ GET request → show form
    conn.close()
    return render_template(
        "add_payment.html",
        patient=patient,
        pending_credit=pending_credit
    )


@app.route("/add_family_member", methods=["POST"])
@login_required
def add_family_member():
    name = request.form["name"].strip()
    age = request.form["age"].strip()
    gender = request.form["gender"]
    mobile = request.form["mobile"].strip()
    address = request.form["address"].strip()

    # BACKEND VALIDATION
    if not is_valid_name(name):
        return "Invalid name. Only letters allowed."

    if not is_valid_age(age):
        return "Invalid age."

    if gender not in ["M", "F", "O"]:
        return "Invalid gender selection."

    if not is_valid_mobile(mobile):
        return "Invalid mobile number."
    if not address:
        return "Address is required."


    conn = get_db()
    cursor = conn.cursor()

    # Contact MUST exist here
    cursor.execute(
        "SELECT id FROM contacts WHERE mobile=?",
        (mobile,)
    )
    contact = cursor.fetchone()

    if not contact:
        conn.close()
        return "Error: Contact not found"

    contact_id = contact[0]

    cursor.execute(
        "INSERT INTO patients (name, age, gender, address, contact_id) VALUES (?, ?, ?, ?, ?)",
        (name, age, gender, address, contact_id)
    )
    conn.commit()

    patient_id = cursor.lastrowid
    conn.close()

    return redirect(url_for("add_visit_page", patient_id=patient_id))

@app.route("/force_add_patient", methods=["POST"])
@login_required
def force_add_patient():
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    contact_id = request.form["contact_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO patients (name, age, gender, contact_id) VALUES (?, ?, ?, ?)",
        (name, age, gender, contact_id)
    )
    conn.commit()

    patient_id = cursor.lastrowid
    conn.close()

    return redirect(url_for("add_visit_page", patient_id=patient_id))

@app.route("/search_page")
@login_required
def search_page():
    return render_template("search_page.html")

@app.route("/search")
@login_required
def search():
    mobile = request.args.get("mobile")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM contacts WHERE mobile=?",
        (mobile,)
    )
    contact = cursor.fetchone()

    if not contact:
        conn.close()
        return "No contact found for this mobile number."

    contact_id = contact[0]

    cursor.execute(
        "SELECT * FROM patients WHERE contact_id=?",
        (contact_id,)
    )
    patients = cursor.fetchall()

    conn.close()

    return render_template(
        "family_patients.html",
        mobile=mobile,
        patients=patients
    )
@app.route("/search_by_name")
@login_required
def search_by_name():
    name = request.args.get("name").strip().lower()

    conn = get_db()
    cursor = conn.cursor()

    # Find patients with similar names (case-insensitive)
    cursor.execute("""
        SELECT patients.id, patients.name, patients.age, patients.gender, patients.address, contacts.mobile

        FROM patients
        JOIN contacts ON patients.contact_id = contacts.id
        WHERE LOWER(patients.name) LIKE ?
    """, ('%' + name + '%',))

    results = cursor.fetchall()
    conn.close()

    return render_template(
        "name_search_results.html",
        query=name,
        patients=results
    )

@app.route("/smart_search")
@login_required
def smart_search():
    query = request.args.get("query", "").strip().lower()

    if not query:
        return "Please enter name, mobile number, or village."

    conn = get_db()
    cursor = conn.cursor()

    # Case 1: Mobile number (all digits)
    if query.isdigit():
        cursor.execute(
            "SELECT id FROM contacts WHERE mobile=?",
            (query,)
        )
        contact = cursor.fetchone()

        if not contact:
            conn.close()
            return "No patient found for this mobile number."

        contact_id = contact[0]

        cursor.execute("""
            SELECT patients.id, patients.name, patients.age, patients.gender,
                   patients.address, contacts.mobile
            FROM patients
            JOIN contacts ON patients.contact_id = contacts.id
            WHERE patients.contact_id=?
        """, (contact_id,))

        patients = cursor.fetchall()
        conn.close()

        return render_template(
            "search_results.html",
            title="Search Results (Mobile)",
            patients=patients
        )

    # Case 2: Name OR Village (text search)
    cursor.execute("""
        SELECT patients.id, patients.name, patients.age, patients.gender,
               patients.address, contacts.mobile
        FROM patients
        JOIN contacts ON patients.contact_id = contacts.id
        WHERE LOWER(patients.name) LIKE ?
           OR LOWER(patients.address) LIKE ?
    """, ('%' + query + '%', '%' + query + '%'))

    patients = cursor.fetchall()
    conn.close()

    return render_template(
        "search_results.html",
        title="Search Results (Name / Village)",
        patients=patients
    )


@app.route("/today")
@login_required
def today_opd():
    conn = get_db()
    cursor = conn.cursor()

    # ===== 🩺 TODAY'S OPD VISITS (FETCH FIRST!) =====
    cursor.execute("""
        SELECT
            visits.id,
            visits.date,
            patients.id,
            patients.name,
            patients.age,
            patients.gender,
            patients.address,
            contacts.mobile,
            visits.fee,
            visits.paid,
            visits.payment_mode
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        JOIN contacts ON patients.contact_id = contacts.id
        WHERE DATE(visits.date, 'localtime') = DATE('now', 'localtime')
          AND visits.symptoms != 'PAYMENT'
            AND is_void = 0
        ORDER BY visits.date DESC
        

    """)
    visits = cursor.fetchall()   # ✅ FETCH NOW (CRITICAL)

    formatted_visits = []
    for v in visits:
        v = list(v)
        v[1] = format_ist_time(v[1])
        formatted_visits.append(v)

    # ===== 💰 TODAY'S MONEY STATS =====

    cursor.execute("""
        SELECT COALESCE(SUM(fee), 0)
        FROM visits
        WHERE DATE(date, 'localtime') = DATE('now', 'localtime')
          AND symptoms != 'PAYMENT'
        AND is_void = 0

    """)
    total_fee_today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(paid), 0)
        FROM visits
        WHERE DATE(date, 'localtime') = DATE('now', 'localtime')
          AND payment_mode = 'CASH'
        AND is_void = 0

    """)
    cash_today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(paid), 0)
        FROM visits
        WHERE DATE(date, 'localtime') = DATE('now', 'localtime')
          AND payment_mode = 'UPI'
        AND is_void = 0

    """)
    upi_today = cursor.fetchone()[0]

    total_collected_today = cash_today + upi_today

    cursor.execute("""
        SELECT COALESCE(SUM(fee - paid), 0)
        FROM visits
        WHERE DATE(date, 'localtime') = DATE('now', 'localtime')
          AND symptoms != 'PAYMENT'
        AND is_void = 0

    """)
    credit_today = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "today_opd.html",
        visits=formatted_visits,
        count=len(formatted_visits),
        total_fee_today=total_fee_today,
        cash_today=cash_today,
        upi_today=upi_today,
        total_collected_today=total_collected_today,
        credit_today=credit_today
    )

@app.route("/payment_register")
@login_required
def payment_register():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # default = today
    if not from_date or not to_date:
        today = datetime.now().strftime("%Y-%m-%d")
        from_date = to_date = today

    conn = get_db()
    cursor = conn.cursor()

    # ---- TRANSACTION ROWS ----
    cursor.execute("""
        SELECT
            visits.date,
            patients.id,
            patients.name,
            contacts.mobile,
            visits.fee,
            visits.paid,
            visits.credit,
            visits.payment_mode,
            visits.symptoms
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        JOIN contacts ON patients.contact_id = contacts.id
        WHERE DATE(visits.date) BETWEEN DATE(?) AND DATE(?)
            AND is_void = 0

        ORDER BY visits.date DESC
        
    """, (from_date, to_date))

    rows = cursor.fetchall()

    # ---- STATS ----
    cursor.execute("""
        SELECT
            COALESCE(SUM(fee),0),
            COALESCE(SUM(paid),0),
            COALESCE(SUM(CASE WHEN payment_mode='CASH' THEN paid ELSE 0 END),0),
            COALESCE(SUM(CASE WHEN payment_mode='UPI' THEN paid ELSE 0 END),0),
            COALESCE(SUM(fee - paid),0)
        FROM visits
        WHERE DATE(date) BETWEEN DATE(?) AND DATE(?)
        AND is_void = 0

    """, (from_date, to_date))

    total_fee, total_paid, cash, upi, credit = cursor.fetchone()
    conn.close()

    return render_template(
        "payment_register.html",
        rows=rows,
        from_date=from_date,
        to_date=to_date,
        total_fee=total_fee,
        total_paid=total_paid,
        cash=cash,
        upi=upi,
        credit=credit
    )


@app.route("/patient_directory")
@login_required
def patient_directory():
    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    # Total patient count
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    total_pages = (total_patients + per_page - 1) // per_page

    # Paginated patients
    cursor.execute("""
        SELECT
            patients.id,
            patients.name,
            patients.age,
            patients.gender,
            patients.address,
            contacts.mobile
        FROM patients
        JOIN contacts ON patients.contact_id = contacts.id
        ORDER BY LOWER(patients.name)
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    patients = cursor.fetchall()
    conn.close()

    return render_template(
        "patient_directory.html",
        patients=patients,
        page=page,
        total_pages=total_pages,
        total_patients=total_patients
    )

@app.route("/opd_by_date")
@login_required
def opd_by_date():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    if not from_date or not to_date:
        return "Please select both dates."

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT visits.id,
           visits.date,
           patients.id,
           patients.name,
           patients.age,
           patients.gender,
           patients.address,
           contacts.mobile
    FROM visits
    JOIN patients ON visits.patient_id = patients.id
    JOIN contacts ON patients.contact_id = contacts.id
    WHERE DATE(visits.date) BETWEEN DATE(?) AND DATE(?)
      AND visits.symptoms != 'PAYMENT'
      AND is_void = 0
    ORDER BY visits.date DESC
    

""", (from_date, to_date))


    visits = cursor.fetchall()
    conn.close()

    return render_template(
        "opd_by_date.html",
        visits=visits,
        from_date=from_date,
        to_date=to_date,
        count=len(visits)
    )

@app.route("/credit_register")
@login_required
def credit_register():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            patients.id,
            patients.name,
            patients.age,
            patients.gender,
            contacts.mobile,
            patients.address,
            COALESCE(SUM(visits.fee),0) AS total_fee,
            COALESCE(SUM(visits.paid),0) AS total_paid,
            COALESCE(SUM(visits.fee),0) - COALESCE(SUM(visits.paid),0) AS pending
        FROM patients
        JOIN contacts ON patients.contact_id = contacts.id
        JOIN visits ON visits.patient_id = patients.id
        GROUP BY patients.id
        HAVING pending > 0
        ORDER BY pending DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return render_template(
        "credit_register.html",
        rows=rows,
        count=len(rows)
    )
@app.route("/compounder")
#@login_required
def compounder_queue():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            visits.id,
            visits.date,
            patients.name,
            patients.age,
            patients.gender,
            visits.advice
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        WHERE DATE(visits.date) = DATE('now')
          AND visits.symptoms != 'PAYMENT'
          AND visits.status = 'PENDING'
        ORDER BY visits.date ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return render_template(
        "compounder_queue.html",
        rows=rows
    )
@app.route("/dispense/<int:visit_id>", methods=["POST"])
def mark_dispensed(visit_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE visits
        SET status = 'DONE'
        WHERE id = ?
    """, (visit_id,))

    conn.commit()
    conn.close()

    return redirect("/compounder")

@app.route("/analytics")
@login_required
def analytics():
    conn = get_db()
    cursor = conn.cursor()

    # Summary cards
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visits")
    total_visits = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM visits
        WHERE DATE(date) = DATE('now')
    """)
    today_opd = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM visits
        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """)
    month_opd = cursor.fetchone()[0]

    # Village-wise patients
    cursor.execute("""
    SELECT 
        COALESCE(address, 'Unknown') AS address,
        COUNT(*)
    FROM patients
    GROUP BY COALESCE(address, 'Unknown')
""")

    raw_village_data = cursor.fetchall()
    village_labels = [row[0] for row in raw_village_data]
    village_counts = [row[1] for row in raw_village_data]


    # Age groups
    cursor.execute("""
    SELECT 
        CASE
            WHEN age IS NULL THEN 'Unknown'
            WHEN age < 13 THEN 'Child'
            WHEN age BETWEEN 13 AND 25 THEN 'Youth'
            WHEN age BETWEEN 26 AND 60 THEN 'Adult'
            ELSE 'Senior'
        END,
        COUNT(*)
    FROM patients
    GROUP BY 1
""")

    raw_age_data = cursor.fetchall()
    age_labels = [row[0] for row in raw_age_data]
    age_counts = [row[1] for row in raw_age_data]

    # New vs repeat
    cursor.execute("""
        SELECT patient_id, COUNT(*) 
        FROM visits
        GROUP BY patient_id
    """)
    visit_counts = cursor.fetchall()

    new_patients = sum(1 for v in visit_counts if v[1] == 1)
    repeat_patients = sum(1 for v in visit_counts if v[1] > 1)

    # OPD trend (last 7 days)
    cursor.execute("""
        SELECT DATE(date), COUNT(*)
        FROM visits
        WHERE DATE(date) >= DATE('now', '-6 days')
        GROUP BY DATE(date)
        ORDER BY DATE(date)
    """)
    trend_data = cursor.fetchall()

    # ===== MONETARY STATS =====

# Total fee billed
    cursor.execute("SELECT COALESCE(SUM(fee),0) FROM visits")
    total_fee = cursor.fetchone()[0]

# Total collected
    cursor.execute("SELECT COALESCE(SUM(paid),0) FROM visits")
    total_collected = cursor.fetchone()[0]

# Cash collected
    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE payment_mode='CASH'
""")
    cash_total = cursor.fetchone()[0]

# UPI collected
    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE payment_mode='UPI'
""")
    upi_total = cursor.fetchone()[0]

# Total pending udhaar
    total_pending = total_fee - total_collected

# Collection trend (last 7 days)
    cursor.execute("""
    SELECT DATE(date), COALESCE(SUM(paid),0)
    FROM visits
    WHERE DATE(date) >= DATE('now', '-6 days')
    GROUP BY DATE(date)
    ORDER BY DATE(date)
""")
    money_trend = cursor.fetchall()

    # ===== TODAY FINANCIALS =====
    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE DATE(date) = DATE('now') AND payment_mode = 'CASH'
""")
    cash_today = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE DATE(date) = DATE('now') AND payment_mode = 'UPI'
""")
    upi_today = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(fee - paid),0)
    FROM visits
    WHERE DATE(date) = DATE('now') AND symptoms != 'PAYMENT'
""")
    credit_today = cursor.fetchone()[0]

    total_collected_today = cash_today + upi_today

    # ===== MONTHLY FINANCIALS =====
    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m','now')
      AND payment_mode = 'CASH'
""")
    cash_month = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m','now')
      AND payment_mode = 'UPI'
""")
    upi_month = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(fee - paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m','now')
      AND symptoms != 'PAYMENT'
""")
    credit_month = cursor.fetchone()[0]

    total_collected_month = cash_month + upi_month

    # Money collection trend (last 7 days)
    cursor.execute("""
    SELECT DATE(date), SUM(paid)
    FROM visits
    WHERE DATE(date) >= DATE('now', '-6 days')
    GROUP BY DATE(date)
    ORDER BY DATE(date)
""")
    money_trend = cursor.fetchall()
    # ===== MONTHLY FINANCIALS =====
    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
      AND payment_mode = 'CASH'
""")
    cash_month = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
      AND payment_mode = 'UPI'
""")
    upi_month = cursor.fetchone()[0]

    total_collected_month = cash_month + upi_month

    cursor.execute("""
    SELECT COALESCE(SUM(fee - paid),0)
    FROM visits
    WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
      AND symptoms != 'PAYMENT'
""")
    credit_month = cursor.fetchone()[0]


    conn.close()

    return render_template(
    "analytics_dashboard.html",

    # ===== SUMMARY =====
    total_patients=total_patients,
    total_visits=total_visits,
    today_opd=today_opd,
    month_opd=month_opd,

    # ===== OVERALL FINANCIAL =====
    total_fee=total_fee,
    total_collected=total_collected,
    cash_total=cash_total,
    upi_total=upi_total,
    total_pending=total_pending,

    # ===== TODAY =====
    cash_today=cash_today,
    upi_today=upi_today,
    total_collected_today=total_collected_today,
    credit_today=credit_today,

    # ===== MONTH =====
    cash_month=cash_month,
    upi_month=upi_month,
    total_collected_month=total_collected_month,
    credit_month=credit_month,

    # ===== CHART DATA =====
    village_labels=village_labels,
    village_counts=village_counts,
    age_labels=age_labels,
    age_counts=age_counts,
    new_patients=new_patients,
    repeat_patients=repeat_patients,
    trend_data=trend_data,
    money_trend=money_trend
)

import hashlib

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

