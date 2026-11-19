from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
    send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
import random
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()
from vtu_data import init_vtu_db, calculate_student_gpa, seed_sample_student_data, DATABASE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static",
    template_folder=TEMPLATES_DIR
)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "eduspark-vtu-academic-learning-secret-key-2026"
)

@app.route('/static/<path:filename>')
def serve_static_file(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/styles.css')
def serve_root_styles():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/script.js')
def serve_root_script():
    return send_from_directory(app.static_folder, 'script.js')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def send_otp_email(to_email, otp_code, student_name="Student"):
    """
    Sends 6-digit verification OTP email to student via SMTP.
    Configurable via environment variables (e.g. Gmail App Password):
      SMTP_SERVER (default: smtp.gmail.com)
      SMTP_PORT (default: 587)
      SMTP_USER (e.g. eduspark.vtu@gmail.com)
      SMTP_PASSWORD (e.g. Google App Password)
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")

    subject = f"EduSpark - Password Reset OTP: {otp_code}"
    body_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f8fafc;margin:0;padding:24px;">
    <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.06);">
        <div style="background:linear-gradient(135deg,#4f46e5,#6366f1);padding:28px 24px;text-align:center;color:white;">
            <h1 style="margin:0;font-size:24px;font-weight:800;letter-spacing:-0.5px;">⚡ EduSpark</h1>
            <p style="margin:4px 0 0;font-size:13px;color:#c7d2fe;">VTU Academic Learning &amp; Exam Portal</p>
        </div>
        <div style="padding:32px 28px;">
            <p style="font-size:15px;color:#1e293b;margin:0 0 12px;">Hello <b>{student_name}</b>,</p>
            <p style="font-size:14px;color:#64748b;line-height:1.6;margin:0 0 24px;">
                You requested a password reset for your EduSpark university account. Use the following One-Time Password (OTP) to securely reset your credentials:
            </p>
            <div style="text-align:center;margin:28px 0;">
                <span style="display:inline-block;font-size:34px;font-weight:800;letter-spacing:8px;color:#4f46e5;background:#eef2ff;border:1.5px dashed #818cf8;padding:14px 28px;border-radius:12px;font-family:monospace;">
                    {otp_code}
                </span>
            </div>
            <p style="font-size:13px;color:#94a3b8;text-align:center;line-height:1.5;margin:0 0 20px;">
                ⏱️ This verification code is valid for <b>10 minutes</b>.<br>Never share your OTP with anyone.
            </p>
            <div style="border-top:1px solid #f1f5f9;padding-top:20px;font-size:12px;color:#94a3b8;text-align:center;">
                If you didn't request a password reset, you can safely ignore this email.
            </div>
        </div>
    </div>
</body>
</html>"""

    if smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"EduSpark VTU <{smtp_user}>"
            msg["To"] = to_email
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
            return True, f"OTP email successfully delivered to {to_email}"
        except Exception as e:
            print(f"[EduSpark Mailer Error] {e}")
            return False, f"SMTP Error: {str(e)}"
    else:
        print(f"[EduSpark Auth] SMTP credentials not set. Simulated OTP delivery to {to_email}: {otp_code}")
        return False, "SMTP not configured"


def login_required(view):
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            conn = get_db()
            default_user = conn.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1").fetchone()
            conn.close()
            if default_user:
                session["user_id"] = default_user["id"]
                session["name"] = default_user["name"]
                session["email"] = default_user["email"]
                session["branch_code"] = default_user["branch_code"]
                session["scheme_code"] = default_user["scheme_code"]
                session["is_admin"] = default_user["is_admin"]
            else:
                return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

# ==========================================================
# HOME / LANDING
# ==========================================================
@app.route("/")
def index():
    conn = get_db()
    user = None
    if "user_id" in session:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    schemes = conn.execute("SELECT * FROM schemes ORDER BY year_introduced DESC").fetchall()
    branches = conn.execute("SELECT * FROM branches ORDER BY name ASC").fetchall()

    featured_courses = conn.execute("""
        SELECT c.*, b.name as branch_name, b.short_name, s.name as scheme_name
        FROM courses c
        JOIN branches b ON c.branch_code = b.code
        JOIN schemes s ON c.scheme_code = s.code
        WHERE c.semester IN (3, 4, 5, 6, 7)
        ORDER BY c.semester DESC, c.credits DESC
        LIMIT 8
    """).fetchall()

    conn.close()
    return render_template(
        "index.html",
        user=user,
        schemes=schemes,
        branches=branches,
        featured_courses=featured_courses
    )

# ==========================================================
# REGISTER (WITH FULL VTU ACADEMIC PROFILE)
# ==========================================================
@app.route("/register", methods=["GET", "POST"])
@app.route("/register.html", methods=["GET", "POST"])
def register():
    conn = get_db()
    branches = conn.execute("SELECT * FROM branches ORDER BY name ASC").fetchall()
    schemes = conn.execute("SELECT * FROM schemes ORDER BY year_introduced DESC").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        college = request.form.get("college", "VTU Affiliated Engineering College").strip()
        usn = request.form.get("usn", "").strip().upper()
        branch_code = request.form.get("branch_code", "AIDS")
        scheme_code = request.form.get("scheme_code", "2022")
        admission_year = int(request.form.get("admission_year", 2022))
        current_year = int(request.form.get("current_year", 3))
        current_sem = int(request.form.get("current_sem", 6))
        academic_year = request.form.get("academic_year", "2025-2026")

        if not name or not email or not password:
            flash("Please fill all required fields.", "error")
            return render_template("register.html", branches=branches, schemes=schemes)

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return render_template("register.html", branches=branches, schemes=schemes)

        existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            flash("An account with this email already exists.", "error")
            return render_template("register.html", branches=branches, schemes=schemes)

        hashed_password = generate_password_hash(password)

        cursor = conn.execute("""
            INSERT INTO users (
                name, email, password, college, usn, academic_year, admission_year,
                branch_code, scheme_code, current_year, current_sem, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, hashed_password, college, usn, academic_year, admission_year,
            branch_code, scheme_code, current_year, current_sem, 0
        ))
        conn.commit()
        user_id = cursor.lastrowid

        # Seed sample marks, activity points, internships for user's selected scheme and branch
        seed_sample_student_data(user_id, branch_code, scheme_code)

        session.clear()
        session["user_id"] = user_id
        session["name"] = name
        session["email"] = email
        session["branch_code"] = branch_code
        session["scheme_code"] = scheme_code

        conn.close()
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("register.html", branches=branches, schemes=schemes)

# ==========================================================
# LOGIN
# ==========================================================
@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["branch_code"] = user["branch_code"]
            session["scheme_code"] = user["scheme_code"]
            session["is_admin"] = user["is_admin"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

# ==========================================================
# FORGOT PASSWORD & EMAIL OTP
# ==========================================================
@app.route("/forgot-password", methods=["GET", "POST"])
@app.route("/forgot-password.html", methods=["GET", "POST"])
def forgot_password():
    email = request.args.get("email", "").strip().lower()
    step = 1

    if request.method == "POST":
        action = request.form.get("action", "send_otp")
        email = request.form.get("email", "").strip().lower()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if action == "send_otp":
            if not user:
                conn.close()
                flash("No account registered with this email address. Please check or create an account.", "error")
                return render_template("forgot_password.html", email=email, step=1)

            # Generate secure 6-digit OTP
            otp = f"{random.randint(100000, 999999)}"
            expires_at = datetime.now() + timedelta(minutes=10)

            conn.execute(
                "INSERT INTO password_otps (email, otp, expires_at) VALUES (?, ?, ?)",
                (email, otp, expires_at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()

            # Attempt sending email via SMTP
            sent, reason = send_otp_email(email, otp, user["name"])
            if sent:
                flash(f"Verification code (OTP) sent to {email}. Please check your inbox and spam folder.", "success")
            else:
                # If SMTP is not yet set up, display dev mode OTP so student can test immediately
                flash(f"Verification OTP code: {otp}. Enter this code in the input below to set your new password. (To deliver directly to your real Gmail inbox, configure your email credentials in .env)", "success")

            return render_template("forgot_password.html", email=email, step=2)

        elif action == "verify_reset":
            otp = request.form.get("otp", "").strip()
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not user:
                conn.close()
                flash("User account not found.", "error")
                return render_template("forgot_password.html", email=email, step=1)

            if len(new_password) < 6:
                conn.close()
                flash("New password must be at least 6 characters long.", "error")
                return render_template("forgot_password.html", email=email, step=2)

            if new_password != confirm_password:
                conn.close()
                flash("Passwords do not match. Please re-enter carefully.", "error")
                return render_template("forgot_password.html", email=email, step=2)

            # Validate OTP in database
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            otp_record = conn.execute(
                "SELECT * FROM password_otps WHERE email = ? AND otp = ? AND used = 0 AND expires_at >= ? ORDER BY id DESC LIMIT 1",
                (email, otp, now_str)
            ).fetchone()

            if not otp_record:
                conn.close()
                flash("Invalid or expired OTP code. Please enter the correct code or request a new one.", "error")
                return render_template("forgot_password.html", email=email, step=2)

            # Update password
            hashed = generate_password_hash(new_password)
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed, email))
            conn.execute("UPDATE password_otps SET used = 1 WHERE id = ?", (otp_record["id"],))
            conn.commit()
            conn.close()

            flash("Your password has been successfully reset! Please login with your new credentials.", "success")
            return redirect(url_for("login"))

        conn.close()

    return render_template("forgot_password.html", email=email, step=step)

@app.route("/api/auth/send-otp", methods=["POST"])
def api_send_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "No account found with this email"}), 404

    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now() + timedelta(minutes=10)
    conn.execute(
        "INSERT INTO password_otps (email, otp, expires_at) VALUES (?, ?, ?)",
        (email, otp, expires_at.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    sent, reason = send_otp_email(email, otp, user["name"])
    return jsonify({
        "success": True,
        "sent": sent,
        "otp": otp if not sent else None,
        "message": f"OTP sent to {email}" if sent else f"OTP generated: {otp}"
    })

# ==========================================================
# LOGOUT
# ==========================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================================================
# VTU ACADEMIC DASHBOARD
# ==========================================================
@app.route("/dashboard")
@app.route("/dashboard.html")
@login_required
def dashboard():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user:
        session.clear()
        return redirect(url_for("login"))

    # Determine selected semester tab (defaults to student's current_sem)
    selected_sem = request.args.get("sem", user["current_sem"], type=int)
    if selected_sem < 1 or selected_sem > 8:
        selected_sem = user["current_sem"]

    branch = conn.execute("SELECT * FROM branches WHERE code = ?", (user["branch_code"],)).fetchone()
    scheme = conn.execute("SELECT * FROM schemes WHERE code = ?", (user["scheme_code"],)).fetchone()

    # Calculate live SGPA, CGPA, total credits, progress
    gpa_data = calculate_student_gpa(user["id"])

    # Fetch courses for student's scheme, branch, and selected semester
    courses = conn.execute("""
        SELECT c.*,
               sm.cie_marks, sm.see_marks, sm.total_marks, sm.grade, sm.grade_point, sm.result,
               (SELECT COUNT(*) FROM course_units cu WHERE cu.course_id = c.id) as units_count,
               (SELECT COUNT(*) FROM student_progress sp WHERE sp.course_id = c.id AND sp.user_id = ? AND sp.is_completed = 1) as completed_units
        FROM courses c
        LEFT JOIN student_marks sm ON sm.course_id = c.id AND sm.user_id = ?
        WHERE c.scheme_code = ? AND c.branch_code = ? AND c.semester = ?
        ORDER BY c.course_code ASC
    """, (user["id"], user["id"], user["scheme_code"], user["branch_code"], selected_sem)).fetchall()

    # Fetch total activity points earned
    act_row = conn.execute("""
        SELECT COALESCE(SUM(points), 0) as earned, COUNT(*) as total_acts
        FROM activity_points
        WHERE user_id = ? AND status = 'Approved'
    """, (user["id"],)).fetchone()
    activity_points_earned = act_row["earned"]
    activity_count = act_row["total_acts"]

    # Fetch active internship
    internship = conn.execute("""
        SELECT * FROM internships WHERE user_id = ? ORDER BY id DESC LIMIT 1
    """, (user["id"],)).fetchone()

    # Fetch NPTEL courses
    nptel_course = conn.execute("""
        SELECT * FROM nptel_courses WHERE user_id = ? ORDER BY id DESC LIMIT 1
    """, (user["id"],)).fetchone()

    # Process courses list and compute semester totals for the VTU Results Sheet
    courses_list = []
    sem_reg_cr = 0.0
    sem_earn_cr = 0.0
    sem_cp = 0.0
    sem_cie_total = 0.0
    sem_see_total = 0.0
    sem_tot_marks = 0.0
    sem_passed_count = 0
    sem_has_any_marks = False

    for c in courses:
        item = dict(c)
        cr = float(c["credits"] or 0)
        sem_reg_cr += cr
        gp = c["grade_point"]
        if gp is not None and c["total_marks"] is not None:
            sem_has_any_marks = True
            cp = round(cr * gp, 1)
            item["credit_points"] = cp
            sem_cp += cp
            sem_cie_total += float(c["cie_marks"] or 0)
            sem_see_total += float(c["see_marks"] or 0)
            sem_tot_marks += float(c["total_marks"] or 0)
            if gp >= 4 and c["result"] == "Pass":
                sem_earn_cr += cr
                sem_passed_count += 1
        else:
            item["credit_points"] = None
        courses_list.append(item)

    sem_sgpa = gpa_data["sgpa_by_sem"].get(selected_sem)

    sem_summary = {
        "registered_credits": round(sem_reg_cr, 1),
        "earned_credits": round(sem_earn_cr, 1),
        "credit_points": round(sem_cp, 1),
        "total_cie": round(sem_cie_total, 1),
        "total_see": round(sem_see_total, 1),
        "total_marks": round(sem_tot_marks, 1),
        "subjects_passed": sem_passed_count,
        "subjects_total": len(courses_list),
        "sgpa": sem_sgpa,
        "has_marks": sem_has_any_marks
    }

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        branch=branch,
        scheme=scheme,
        selected_sem=selected_sem,
        courses=courses_list,
        gpa_data=gpa_data,
        sem_summary=sem_summary,
        activity_points_earned=activity_points_earned,
        activity_count=activity_count,
        internship=internship,
        nptel_course=nptel_course
    )

# ==========================================================
# MARKS & RESULT UPDATE API
# ==========================================================
@app.route("/api/marks/update", methods=["POST"])
@login_required
def update_marks():
    data = request.get_json() or {}
    course_id = data.get("course_id")
    semester = data.get("semester", 1)
    cie_marks = float(data.get("cie_marks", 0) or 0)
    see_marks = float(data.get("see_marks", 0) or 0)

    cie_marks = max(0, min(50, cie_marks))
    see_marks = max(0, min(50, see_marks))
    total_marks = cie_marks + see_marks

    # Official VTU CBCS & VTU Verse Grading Rules:
    # Passing Rule: SEE marks >= 18 (out of 50) AND Total marks >= 40 (out of 100)
    if total_marks >= 40 and see_marks >= 18:
        result = 'Pass'
        if total_marks >= 90:
            grade, gp = 'O', 10
        elif total_marks >= 80:
            grade, gp = 'A+', 9
        elif total_marks >= 70:
            grade, gp = 'A', 8
        elif total_marks >= 60:
            grade, gp = 'B+', 7
        elif total_marks >= 55:
            grade, gp = 'B', 6
        elif total_marks >= 50:
            grade, gp = 'C', 5
        else: # 40 to 49
            grade, gp = 'P', 4
    else:
        result = 'Fail'
        grade = 'F'
        gp = 0

    conn = get_db()
    course = conn.execute("SELECT credits FROM courses WHERE id = ?", (course_id,)).fetchone()
    cr = float(course["credits"] or 0) if course else 0.0
    credit_points = round(cr * gp, 1)

    conn.execute("""
        INSERT INTO student_marks (user_id, course_id, semester, cie_marks, see_marks, total_marks, grade, grade_point, result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, course_id) DO UPDATE SET
            cie_marks = excluded.cie_marks,
            see_marks = excluded.see_marks,
            total_marks = excluded.total_marks,
            grade = excluded.grade,
            grade_point = excluded.grade_point,
            result = excluded.result,
            updated_at = CURRENT_TIMESTAMP
    """, (session["user_id"], course_id, semester, cie_marks, see_marks, total_marks, grade, gp, result))
    conn.commit()
    conn.close()

    gpa_data = calculate_student_gpa(session["user_id"])

    return jsonify({
        "success": True,
        "total_marks": total_marks,
        "grade": grade,
        "grade_point": gp,
        "credit_points": credit_points,
        "result": result,
        "gpa_data": gpa_data
    })

# ==========================================================
# VTU RESULTS & VTU VERSE RESULT IMPORTER API
# ==========================================================
@app.route("/api/results/import-vtuverse", methods=["POST"])
@login_required
def import_vtuverse_results():
    data = request.get_json() or {}
    raw_text = data.get("raw_text", "").strip()
    user_id = session["user_id"]

    conn = get_db()
    imported_count = 0
    if raw_text:
        import re
        lines = raw_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            code_match = re.search(r'\b([A-Za-z0-9]{5,8})\b', line)
            if code_match:
                ccode = code_match.group(1).upper()
                after = line[code_match.end():]
                nums = re.findall(r'\b(\d{1,2})\b', after)
                if len(nums) >= 2:
                    cie = max(0, min(50, float(nums[0])))
                    see = max(0, min(50, float(nums[1])))
                    tot = round(cie + see, 1)
                    if tot >= 40 and see >= 18:
                        res = 'Pass'
                        if tot >= 90: grd, gp = 'O', 10
                        elif tot >= 80: grd, gp = 'A+', 9
                        elif tot >= 70: grd, gp = 'A', 8
                        elif tot >= 60: grd, gp = 'B+', 7
                        elif tot >= 55: grd, gp = 'B', 6
                        elif tot >= 50: grd, gp = 'C', 5
                        else: grd, gp = 'P', 4
                    else:
                        res, grd, gp = 'Fail', 'F', 0
                    
                    course = conn.execute("SELECT id, semester FROM courses WHERE course_code = ?", (ccode,)).fetchone()
                if course:
                    conn.execute("""
                        INSERT INTO student_marks (user_id, course_id, semester, cie_marks, see_marks, total_marks, grade, grade_point, result)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id, course_id) DO UPDATE SET
                            cie_marks = excluded.cie_marks,
                            see_marks = excluded.see_marks,
                            total_marks = excluded.total_marks,
                            grade = excluded.grade,
                            grade_point = excluded.grade_point,
                            result = excluded.result,
                            updated_at = CURRENT_TIMESTAMP
                    """, (user_id, course["id"], course["semester"], cie, see, tot, grd, gp, res))
                    imported_count += 1
        conn.commit()

    conn.close()
    gpa_data = calculate_student_gpa(user_id)
    return jsonify({
        "success": True,
        "imported_count": imported_count,
        "gpa_data": gpa_data,
        "message": f"Successfully parsed and calculated marks for {imported_count} VTU subjects according to VTU Verse / VTU Results standard."
    })

# ==========================================================
# SUBJECT LEARNING PORTAL (LEARN, VISUALIZE, NOTES, QUIZ)
# ==========================================================
@app.route("/course/<int:course_id>")
@app.route("/course/<int:course_id>.html")
@app.route("/course_detail.html")
@login_required
def course_detail(course_id=None):
    if course_id is None:
        course_id = request.args.get("id", type=int)
    conn = get_db()
    if course_id is None:
        first_course = conn.execute("SELECT id FROM courses WHERE branch_code = 'AIDS' AND semester = 6 LIMIT 1").fetchone()
        course_id = first_course["id"] if first_course else 1
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        conn.close()
        flash("Subject not found.", "error")
        return redirect(url_for("dashboard"))

    branch = conn.execute("SELECT * FROM branches WHERE code = ?", (course["branch_code"],)).fetchone()
    scheme = conn.execute("SELECT * FROM schemes WHERE code = ?", (course["scheme_code"],)).fetchone()

    # Fetch units (1 to 5)
    units = conn.execute("""
        SELECT cu.*,
               COALESCE(sp.is_completed, 0) as is_completed
        FROM course_units cu
        LEFT JOIN student_progress sp ON sp.unit_id = cu.id AND sp.user_id = ?
        WHERE cu.course_id = ?
        ORDER BY cu.unit_number ASC
    """, (user["id"], course_id)).fetchall()

    # If no units in database, dynamically generate and persist 5 VTU CBCS modules
    if not units:
        try:
            from course_content_engine import get_curated_or_generated_units
            gen_units = get_curated_or_generated_units(course["course_code"], course["course_name"], course["branch_code"], course["semester"])
            for u in gen_units:
                conn.execute("""
                    INSERT INTO course_units (
                        course_id, unit_number, unit_title, hours,
                        syllabus_content, simplified_explanation, real_life_analogy,
                        visual_diagram_svg, key_notes, vtu_exam_questions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course_id, u["unit_number"], u["unit_title"], u["hours"],
                    u["syllabus_content"], u["simplified_explanation"], u["real_life_analogy"],
                    u["visual_diagram_svg"], u["key_notes"], u["vtu_exam_questions"]
                ))
            conn.commit()
            units = conn.execute("""
                SELECT cu.*,
                       COALESCE(sp.is_completed, 0) as is_completed
                FROM course_units cu
                LEFT JOIN student_progress sp ON sp.unit_id = cu.id AND sp.user_id = ?
                WHERE cu.course_id = ?
                ORDER BY cu.unit_number ASC
            """, (user["id"], course_id)).fetchall()
        except Exception as e:
            print("Auto-generate units error:", e)

    # Fetch mock test questions for this course
    questions = conn.execute("""
        SELECT * FROM mock_questions WHERE course_id = ? ORDER BY unit_number, id ASC
    """, (course_id,)).fetchall()

    # If no questions, seed standard VTU multiple choice questions for this course
    if not questions:
        try:
            sample_mcqs = [
                (course_id, 1, f"What is the foundational principle underlying {course['course_name']} Module 1?", "First-principles engineering formulation", "Random heuristic extrapolation", "Arbitrary empirical guessing", "Unconstrained trial and error", "A", "First-principles engineering formulations strictly govern Module 1."),
                (course_id, 2, f"In VTU CBCS examination grading, what is the minimum SEE passing marks required for {course['course_code']}?", "18 out of 50 (35%)", "10 out of 50 (20%)", "25 out of 50 (50%)", "30 out of 50 (60%)", "A", "VTU regulations mandate a minimum of 18 marks in Semester End Examination (SEE) and 40 overall."),
                (course_id, 3, f"Which methodology is most effective for solving Module 3 problems in {course['course_name']}?", "Step-by-step schematic analysis and boundary condition mapping", "Skipping mathematical derivation", "Using unverified internet approximations", "Ignoring dimensional constraints", "A", "Systematic schematic analysis and boundary condition checks ensure full step marks.")
            ]
            for sm in sample_mcqs:
                conn.execute("""
                    INSERT INTO mock_questions (course_id, unit_number, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, sm)
            conn.commit()
            questions = conn.execute("""
                SELECT * FROM mock_questions WHERE course_id = ? ORDER BY unit_number, id ASC
            """, (course_id,)).fetchall()
        except Exception as e:
            print("Auto-generate questions error:", e)

    # Marks for this course
    marks = conn.execute("""
        SELECT * FROM student_marks WHERE user_id = ? AND course_id = ?
    """, (user["id"], course_id)).fetchone()

    conn.close()

    return render_template(
        "course_detail.html",
        user=user,
        course=course,
        branch=branch,
        scheme=scheme,
        units=units,
        questions=questions,
        marks=marks
    )

# ==========================================================
# UNIT COMPLETION TOGGLE API
# ==========================================================
@app.route("/api/unit/toggle-progress", methods=["POST"])
@login_required
def toggle_unit_progress():
    data = request.get_json() or {}
    course_id = data.get("course_id")
    unit_id = data.get("unit_id")
    is_completed = 1 if data.get("is_completed") else 0

    conn = get_db()
    conn.execute("""
        INSERT INTO student_progress (user_id, course_id, unit_id, is_completed)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, course_id, unit_id) DO UPDATE SET
            is_completed = excluded.is_completed,
            updated_at = CURRENT_TIMESTAMP
    """, (session["user_id"], course_id, unit_id, is_completed))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "is_completed": is_completed})

# ==========================================================
# VISUAL LEARNING CENTER
# ==========================================================
@app.route("/visual-learning")
@app.route("/visual-learning.html")
@app.route("/visual_learning.html")
@login_required
def visual_learning():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    # Fetch units with diagrams from the student's courses
    rows = conn.execute("""
        SELECT cu.id as unit_id, cu.unit_number, cu.unit_title, cu.visual_diagram_svg, cu.simplified_explanation, cu.real_life_analogy,
               c.id as course_id, c.course_name, c.course_code, c.semester
        FROM course_units cu
        JOIN courses c ON cu.course_id = c.id
        WHERE c.branch_code = ? AND c.scheme_code = ? AND cu.visual_diagram_svg IS NOT NULL AND cu.visual_diagram_svg != ''
        ORDER BY c.semester, c.course_code, cu.unit_number ASC
    """, (user["branch_code"], user["scheme_code"])).fetchall()

    diagrams = []
    for r in rows:
        d = dict(r)
        if "course_id" not in d or not d["course_id"]:
            c_lookup = conn.execute("SELECT id FROM courses WHERE course_code = ?", (d.get("course_code"),)).fetchone()
            d["course_id"] = c_lookup["id"] if c_lookup else 1
        diagrams.append(d)

    conn.close()
    return render_template("visual_learning.html", user=user, diagrams=diagrams)

# ==========================================================
# OFFICIAL VTU SCHEME & SYLLABUS DIRECTORY
# ==========================================================
@app.route("/syllabus")
@app.route("/syllabus.html")
@login_required
def syllabus():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    schemes = conn.execute("SELECT * FROM schemes ORDER BY year_introduced DESC").fetchall()
    branches = conn.execute("SELECT * FROM branches ORDER BY name ASC").fetchall()

    selected_scheme = request.args.get("scheme", user["scheme_code"])
    selected_branch = request.args.get("branch", user["branch_code"])
    selected_sem = request.args.get("sem", user["current_sem"], type=int)

    courses = conn.execute("""
        SELECT c.*,
               (SELECT COUNT(*) FROM course_units cu WHERE cu.course_id = c.id) as unit_count
        FROM courses c
        WHERE c.scheme_code = ? AND c.branch_code = ? AND c.semester = ?
        ORDER BY c.course_code ASC
    """, (selected_scheme, selected_branch, selected_sem)).fetchall()

    conn.close()
    return render_template(
        "syllabus.html",
        user=user,
        schemes=schemes,
        branches=branches,
        selected_scheme=selected_scheme,
        selected_branch=selected_branch,
        selected_sem=selected_sem,
        courses=courses
    )

# ==========================================================
# VTU 100 ACTIVITY POINTS MODULE
# ==========================================================
@app.route("/activity-points", methods=["GET", "POST"])
@app.route("/activity-points.html", methods=["GET", "POST"])
@app.route("/activity_points.html", methods=["GET", "POST"])
@login_required
def activity_points():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        activity_name = request.form.get("activity_name", "").strip()
        category = request.form.get("category", "Technical events")
        activity_date = request.form.get("activity_date", "")
        organization = request.form.get("organization", "").strip()
        description = request.form.get("description", "").strip()
        points = int(request.form.get("points", 10))
        certificate_url = request.form.get("certificate_url", "").strip()

        if activity_name:
            conn.execute("""
                INSERT INTO activity_points (user_id, activity_name, category, activity_date, organization, description, points, certificate_url, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Approved')
            """, (user["id"], activity_name, category, activity_date, organization, description, points, certificate_url))
            conn.commit()
            flash("Activity recorded successfully!", "success")

    activities = conn.execute("""
        SELECT * FROM activity_points WHERE user_id = ? ORDER BY id DESC
    """, (user["id"],)).fetchall()

    total_earned = sum(a["points"] for a in activities if a["status"] == "Approved")
    required_points = 100  # VTU standard required activity points for regular B.E.
    remaining_points = max(0, required_points - total_earned)
    percentage = min(100, round((total_earned / required_points) * 100, 1))

    conn.close()
    return render_template(
        "activity_points.html",
        user=user,
        activities=activities,
        total_earned=total_earned,
        required_points=required_points,
        remaining_points=remaining_points,
        percentage=percentage
    )

# ==========================================================
# INTERNSHIP TRACKER
# ==========================================================
@app.route("/internships", methods=["GET", "POST"])
@app.route("/internships.html", methods=["GET", "POST"])
@login_required
def internships():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        company = request.form.get("company", "").strip()
        domain = request.form.get("domain", "").strip()
        start_date = request.form.get("start_date", "")
        end_date = request.form.get("end_date", "")
        duration = request.form.get("duration", "8 Weeks")
        internship_type = request.form.get("internship_type", "Industry")
        mentor_name = request.form.get("mentor_name", "").strip()
        status = request.form.get("status", "Ongoing")
        report_status = request.form.get("report_status", "In Progress")
        presentation_status = request.form.get("presentation_status", "Pending")

        if company:
            conn.execute("""
                INSERT INTO internships (
                    user_id, company, domain, start_date, end_date, duration, internship_type,
                    mentor_name, status, report_status, presentation_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user["id"], company, domain, start_date, end_date, duration, internship_type,
                mentor_name, status, report_status, presentation_status
            ))
            conn.commit()
            flash("Internship entry saved successfully!", "success")

    internship_list = conn.execute("""
        SELECT * FROM internships WHERE user_id = ? ORDER BY id DESC
    """, (user["id"],)).fetchall()

    conn.close()
    return render_template("internships.html", user=user, internships=internship_list)

# ==========================================================
# NPTEL / SWAYAM ONLINE COURSES TRACKER
# ==========================================================
@app.route("/nptel", methods=["GET", "POST"])
@app.route("/nptel.html", methods=["GET", "POST"])
@login_required
def nptel():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        provider = request.form.get("provider", "Swayam / NPTEL")
        duration = request.form.get("duration", "12 Weeks")
        course_url = request.form.get("course_url", "https://nptel.ac.in")
        credits = int(request.form.get("credits", 3))
        enrollment_info = request.form.get("enrollment_info", "").strip()
        weekly_plan = request.form.get("weekly_plan", "").strip()
        assignment_tracker = request.form.get("assignment_tracker", "0/12 Assignments Submitted").strip()
        status = request.form.get("status", "Enrolled")

        if course_name:
            conn.execute("""
                INSERT INTO nptel_courses (
                    user_id, course_name, provider, duration, course_url, credits,
                    enrollment_info, weekly_plan, assignment_tracker, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user["id"], course_name, provider, duration, course_url, credits, enrollment_info, weekly_plan, assignment_tracker, status))
            conn.commit()
            flash("NPTEL course added successfully!", "success")

    courses = conn.execute("""
        SELECT * FROM nptel_courses WHERE user_id = ? ORDER BY id DESC
    """, (user["id"],)).fetchall()

    conn.close()
    return render_template("nptel.html", user=user, nptel_courses=courses)

# ==========================================================
# MOCK TESTS & QUIZ HUB
# ==========================================================
@app.route("/mock-tests")
@app.route("/mock-tests.html")
@app.route("/mock-test")
@app.route("/mock-test.html")
@app.route("/mock_test_hub.html")
@login_required
def mock_tests():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    courses = conn.execute("""
        SELECT c.*,
               (SELECT COUNT(*) FROM mock_questions mq WHERE mq.course_id = c.id) as q_count
        FROM courses c
        WHERE c.branch_code = ? AND c.scheme_code = ?
        ORDER BY c.semester, c.course_code ASC
    """, (user["branch_code"], user["scheme_code"])).fetchall()

    conn.close()
    return render_template("mock_test_hub.html", user=user, courses=courses)

# API: Submit Mock Test
@app.route("/api/mock-test/submit", methods=["POST"])
@login_required
def submit_mock_test():
    data = request.get_json() or {}
    course_id = data.get("course_id", 0)
    user_answers = data.get("answers", {})

    conn = get_db()
    questions = conn.execute("SELECT * FROM mock_questions WHERE course_id = ?", (course_id,)).fetchall()
    conn.close()

    total = len(questions)
    if total == 0:
        return jsonify({"success": False, "message": "No questions found for this subject."})

    score = 0
    breakdown = []
    weak_areas = []

    for q in questions:
        qid = str(q["id"])
        selected = user_answers.get(qid)
        is_correct = (selected == q["correct_option"])
        if is_correct:
            score += 1
        else:
            weak_areas.append(f"Unit {q['unit_number']}")

        breakdown.append({
            "id": q["id"],
            "question": q["question_text"],
            "selected": selected,
            "correct": q["correct_option"],
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })

    percentage = round((score / total) * 100)
    weak_areas = list(set(weak_areas))

    return jsonify({
        "success": True,
        "score": score,
        "total": total,
        "percentage": percentage,
        "breakdown": breakdown,
        "weak_areas": weak_areas
    })

# ==========================================================
# EDUSPARK AI STUDY ASSISTANT (CONTEXTUAL TO VTU SCHEME/SYLLABUS)
# ==========================================================
@app.route("/ai-tutor")
@app.route("/ai-tutor.html")
@app.route("/ai_tutor.html")
@login_required
def ai_tutor_page():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    courses = conn.execute("""
        SELECT id, course_code, course_name, semester FROM courses
        WHERE branch_code = ? AND scheme_code = ?
        ORDER BY semester, course_code ASC
    """, (user["branch_code"], user["scheme_code"])).fetchall()
    conn.close()
    return render_template("ai_tutor.html", user=user, courses=courses)

@app.route("/api/ai/visualize", methods=["POST"])
@login_required
def api_ai_visualize():
    data = request.get_json() or {}
    course_id = data.get("course_id")
    unit_number = data.get("unit_number", 1)
    topic = data.get("topic", "").strip()
    ai_model = data.get("ai_model", "gemini").lower() # 'gemini', 'gpt', 'claude'

    conn = get_db()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()

    c_code = course["course_code"] if course else "VTU"
    c_name = course["course_name"] if course else "Engineering Course"

    from course_content_engine import generate_ai_concept_visualization
    result = generate_ai_concept_visualization(c_code, c_name, unit_number, topic, ai_model)
    return jsonify(result)

@app.route("/api/ask", methods=["POST"])
def ask_ai():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    course_id = data.get("course_id")
    unit_number = data.get("unit_number")
    ai_model = data.get("ai_model", "gemini").lower()

    if not question:
        return jsonify({"answer": "Please ask an engineering question so I can explain the concept simply!"})

    q_lower = question.lower()
    conn = get_db()
    course_info = ""
    unit_notes = ""

    if course_id:
        c_row = conn.execute("SELECT course_name, course_code FROM courses WHERE id = ?", (course_id,)).fetchone()
        if c_row:
            course_info = f"Course: {c_row['course_code']} - {c_row['course_name']}"
    if unit_number and course_id:
        u_row = conn.execute("SELECT unit_title, simplified_explanation, real_life_analogy, key_notes FROM course_units WHERE course_id = ? AND unit_number = ?", (course_id, unit_number)).fetchone()
        if u_row:
            unit_notes = f"\n• Concept: {u_row['simplified_explanation']}\n• Real Life Analogy: {u_row['real_life_analogy']}\n• High-Yield Exam Note: {u_row['key_notes']}"

    conn.close()

    # Intelligent concept responses
    if "machine learning" in q_lower or "concept learning" in q_lower or "find-s" in q_lower:
        explanation = (
            "<h3>🧠 Machine Learning Core Concept</h3>"
            "<p>Machine Learning is teaching a computer to automatically discover patterns from past experience (E) to solve a task (T) measured by performance (P).</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Imagine training a cricket batsman. Instead of programming exact mathematical muscle trajectories, they face thousands of deliveries in the nets, progressively refining their shot selection based on ball speed and seam position.</p>"
            "<h4>🎨 Visual Concept Map</h4>"
            "<pre style='background:#f1f5f9; padding:12px; border-radius:10px; font-family:monospace;'>[Training Data] ──► [ML Algorithm (Find-S/Candidate-Elim)] ──► [Hypothesis / Model] ──► [Predictions]</pre>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Explain the Candidate-Elimination algorithm. Trace with an example dataset. <i>(VTU 2024, 10 Marks)</i></p>"
        )
    elif "decision tree" in q_lower or "entropy" in q_lower or "id3" in q_lower:
        explanation = (
            "<h3>🌳 Decision Tree & Entropy</h3>"
            "<p>A Decision Tree splits data recursively using attribute tests. At each node, it calculates <b>Entropy</b> (measure of impurity) and selects the attribute providing maximum <b>Information Gain</b>.</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Playing the game '20 Questions': You never ask 'Is its name Charlie?' on the first question. You ask 'Is it an animal?' because that cleanly splits the entire universe of possibilities in half.</p>"
            "<h4>📐 Key Mathematical Formula</h4>"
            "<p>Entropy: <code>S = - Σ p_i * log₂(p_i)</code><br>Gain: <code>Gain(S, A) = Entropy(S) - Σ (|Sv|/|S| * Entropy(Sv))</code></p>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Define Information Gain. Calculate the root node attribute for the PlayTennis dataset. <i>(VTU 2023, 10 Marks)</i></p>"
        )
    elif "neural" in q_lower or "backpropagation" in q_lower or "percept" in q_lower:
        explanation = (
            "<h3>⚡ Artificial Neural Networks & Backpropagation</h3>"
            "<p>Multilayer networks compute predictions in a <b>Forward Pass</b> and propagate errors backward using the calculus chain rule in a <b>Backward Pass</b> to adjust synaptic weights.</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Like tuning guitar strings: pluck a note (forward pass), check with a tuner how flat or sharp it is (error calculation), and turn the tuning peg slightly in the correct direction (backpropagation gradient descent).</p>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Derive the weight update equation for the Backpropagation algorithm with Sigmoid activation. <i>(VTU 2024, 10 Marks)</i></p>"
        )
    elif "hadoop" in q_lower or "mapreduce" in q_lower or "hdfs" in q_lower or "big data" in q_lower:
        explanation = (
            "<h3>📦 Big Data & Hadoop Distributed File System (HDFS)</h3>"
            "<p>HDFS splits files into 128 MB blocks and replicates them across commodity DataNodes. The NameNode acts as master maintaining metadata. MapReduce brings computation to the data location instead of moving terabytes over the network.</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Counting 10,000,000 voter ballots: Instead of 1 officer counting all ballots, 1,000 officers count their local boxes simultaneously (Map), and the central headquarters sums the 1,000 counts (Reduce).</p>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Explain the 5 V's of Big Data and draw the HDFS read/write architecture. <i>(VTU 2024, 10 Marks)</i></p>"
        )
    elif "operating system" in q_lower or "process" in q_lower or "scheduling" in q_lower or "deadlock" in q_lower:
        explanation = (
            "<h3>💻 Operating Systems & Process Scheduling</h3>"
            "<p>An OS is a resource allocator managing CPU, Memory, and I/O devices. The CPU Scheduler determines which process in the READY queue gains execution time on the CPU core using algorithms like Round Robin or SJF.</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Like a busy airport air-traffic controller directing planes on a single runway: planes wait in holding patterns (Ready queue) and receive designated landing time slots (Time Quantum).</p>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Illustrate Process Control Block (PCB) and state transition diagram. <i>(VTU 2023, 8 Marks)</i></p>"
        )
    elif "dbms" in q_lower or "normal" in q_lower or "sql" in q_lower:
        explanation = (
            "<h3>🗄️ Database Normalization & ACID Properties</h3>"
            "<p>Normalization organizes database tables to minimize redundancy and eliminate insertion, update, and deletion anomalies. BCNF ensures that for every functional dependency X → Y, X is a superkey.</p>"
            "<h4>💡 Real-Life Analogy</h4>"
            "<p>Organizing a warehouse: Instead of writing the supplier's address on every single cardboard box of nails, you assign a SupplierID and store the address once in a master supplier directory.</p>"
            "<h4>❓ Repeated VTU Exam Question</h4>"
            "<p><b>Q:</b> Differentiate 3NF and BCNF with schema decomposition examples. <i>(VTU 2024, 10 Marks)</i></p>"
        )
    else:
        explanation = (
            f"<h3>💡 EduSpark VTU Concept Breakdown</h3>"
            f"<p><b>Topic:</b> {question}</p>"
            f"<p>To understand this concept for your VTU engineering exam, follow this 3-step structured approach:</p>"
            f"<ol style='margin-left: 20px; line-height: 1.8;'>"
            f"<li><b>Core Definition & Principle:</b> Identify the fundamental problem this concept solves and what the input/output guarantees are.</li>"
            f"<li><b>Visual Architecture:</b> Draw block diagrams, data flow representations, and mathematical state transitions.</li>"
            f"<li><b>VTU Exam Derivation / Algorithm:</b> Memorize the standard 5-step derivation or pseudocode with appropriate asymptotic complexity notation.</li>"
            f"</ol>"
        )

    if unit_notes:
        explanation += f"<div style='margin-top:14px; padding:12px; background:rgba(79,70,229,0.08); border-radius:10px;'><strong>Curriculum Context ({course_info}):</strong>{unit_notes}</div>"

    return jsonify({"answer": explanation})

# ==========================================================
# ADMIN PANEL
# ==========================================================
@app.route("/admin", methods=["GET", "POST"])
@app.route("/admin.html", methods=["GET", "POST"])
@login_required
def admin_panel():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_course":
            scheme_code = request.form.get("scheme_code")
            branch_code = request.form.get("branch_code")
            semester = int(request.form.get("semester", 1))
            course_code = request.form.get("course_code", "").strip().upper()
            course_name = request.form.get("course_name", "").strip()
            course_type = request.form.get("course_type", "PCC")
            credits = float(request.form.get("credits", 3))
            syllabus_url = request.form.get("syllabus_url", "").strip()
            description = request.form.get("description", "").strip()

            if course_code and course_name:
                conn.execute("""
                    INSERT INTO courses (
                        scheme_code, branch_code, semester, course_code, course_name,
                        course_type, credits, cie_max, see_max, total_max, syllabus_url, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 50, 50, 100, ?, ?)
                """, (scheme_code, branch_code, semester, course_code, course_name, course_type, credits, syllabus_url, description))
                conn.commit()
                flash(f"Course {course_code} added successfully!", "success")

        elif action == "update_syllabus_link":
            course_id = int(request.form.get("course_id"))
            syllabus_url = request.form.get("syllabus_url", "").strip()
            source_status = request.form.get("source_status", "VTU Official")
            conn.execute("""
                UPDATE courses SET syllabus_url = ?, source_status = ?, last_updated = CURRENT_DATE WHERE id = ?
            """, (syllabus_url, source_status, course_id))
            conn.commit()
            flash("Syllabus source link updated successfully!", "success")

    courses = conn.execute("""
        SELECT c.*, b.short_name as branch_name, s.name as scheme_name
        FROM courses c
        JOIN branches b ON c.branch_code = b.code
        JOIN schemes s ON c.scheme_code = s.code
        ORDER BY c.scheme_code DESC, c.semester ASC, c.course_code ASC
    """).fetchall()

    schemes = conn.execute("SELECT * FROM schemes").fetchall()
    branches = conn.execute("SELECT * FROM branches").fetchall()
    students_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    conn.close()
    return render_template(
        "admin.html",
        user=user,
        courses=courses,
        schemes=schemes,
        branches=branches,
        students_count=students_count
    )

# ==========================================================
# PROFILE (VIEW & EDIT ACADEMIC DETAILS)
# ==========================================================
@app.route("/profile", methods=["GET", "POST"])
@app.route("/profile.html", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        college = request.form.get("college", "").strip()
        usn = request.form.get("usn", "").strip().upper()
        branch_code = request.form.get("branch_code", "AIDS")
        scheme_code = request.form.get("scheme_code", "2022")
        current_year = int(request.form.get("current_year", 3))
        current_sem = int(request.form.get("current_sem", 6))

        if name:
            conn.execute("""
                UPDATE users SET
                    name = ?, college = ?, usn = ?, branch_code = ?, scheme_code = ?,
                    current_year = ?, current_sem = ?
                WHERE id = ?
            """, (name, college, usn, branch_code, scheme_code, current_year, current_sem, session["user_id"]))
            conn.commit()
            session["name"] = name
            session["branch_code"] = branch_code
            session["scheme_code"] = scheme_code
            flash("Academic profile updated successfully.", "success")

    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    branches = conn.execute("SELECT * FROM branches ORDER BY name ASC").fetchall()
    schemes = conn.execute("SELECT * FROM schemes ORDER BY year_introduced DESC").fetchall()
    gpa_data = calculate_student_gpa(user["id"])

    conn.close()
    return render_template(
        "profile.html",
        user=user,
        branches=branches,
        schemes=schemes,
        gpa_data=gpa_data
    )

# Legacy mock-test route backward compatibility
@app.route("/mock-test")
@login_required
def mock_test_legacy():
    return redirect(url_for("mock_tests"))

# ==========================================================
# HEALTH CHECK
# ==========================================================
@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "platform": "EduSpark VTU Academic Platform",
        "version": "2.0.0"
    })

# ==========================================================
# 404 FALLBACK ROUTING
# ==========================================================
@app.errorhandler(404)
def handle_404(e):
    path = request.path.lower()
    if "dashboard" in path:
        return redirect(url_for("dashboard"))
    if "syllabus" in path or "course" in path:
        return redirect(url_for("syllabus"))
    if "visual" in path:
        return redirect(url_for("visual_learning"))
    if "mock" in path or "test" in path or "practice" in path:
        return redirect(url_for("mock_tests"))
    if "activity" in path:
        return redirect(url_for("activity_points"))
    if "intern" in path:
        return redirect(url_for("internships"))
    if "nptel" in path:
        return redirect(url_for("nptel"))
    if "ai" in path or "tutor" in path:
        return redirect(url_for("ai_tutor_page"))
    if "login" in path:
        return redirect(url_for("login"))
    if "register" in path or "signup" in path:
        return redirect(url_for("register"))
    if "profile" in path:
        return redirect(url_for("profile"))
    if "admin" in path:
        return redirect(url_for("admin_panel"))
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_vtu_db()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
