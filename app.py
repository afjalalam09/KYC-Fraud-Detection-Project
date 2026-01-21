from flask import Flask, jsonify, render_template, request
from services.cv_service import extract_text
from services.fraud_service import fraud_check
from db import get_db_connection
import os
from services.aadhaar_parser import extract_name_address
from services.image_quality import is_blurry
from services.data_masking import mask_aadhaar
from services.aadhaar_hash import extract_and_hash_aadhaar
from services.duplicate_check import is_duplicate
from services.fraud_score import calculate_fraud_score, get_alert_level
from flask import  redirect, session, url_for
from services.auth_utils import hash_password
from services.auth_utils import verify_password
import pandas as pd
from flask import Response
from fpdf import FPDF
import datetime
from services.pincode_service import extract_pincode, validate_pincode



def clean_text(text):
    if text is None:
        return ""
    return (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("–", "-")
            .replace("—", "-")
            .encode("latin-1", "ignore")
            .decode("latin-1")
    )



app = Flask(__name__)
app.secret_key = "super-secret-key"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Home Route
@app.route("/")
def home():
    return render_template("index.html")


# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = hash_password(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s,%s)",
                (username, hashed)
            )
            conn.commit()
        except:
            return "User already exists"
        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html")


# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and verify_password(user["password_hash"], password):
            session["user"] = user["username"]
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


# Log Out Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# Dashboard Route
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    latest_record = None

    if request.method == "POST":
        file = request.files["aadhaar"]
        path = os.path.join("uploads", file.filename)
        file.save(path)

        # Image quality check
        blurry = is_blurry(path)

        # OCR
        extracted_text = extract_text(path)
        masked_text = mask_aadhaar(extracted_text)

        # PIN extraction
        pin = extract_pincode(extracted_text)

        # PIN validation
        pin_valid, state = validate_pincode(pin)

        pin_status = "Valid" if pin_valid else "Invalid" 

        # if not pin_valid:
        #     fraud_score += 15

        # Name & Address
        name, address = extract_name_address(masked_text)

        # Aadhaar hash & duplicate
        aadhaar_hash = extract_and_hash_aadhaar(extracted_text)
        duplicate_flag = is_duplicate(aadhaar_hash)
        duplicate_text = "Yes" if duplicate_flag else "No"




        # Fraud Score
        fraud_score, risk_level = calculate_fraud_score(
            is_duplicate=duplicate_flag,
            is_blurry=blurry,
            text_length=len(masked_text),
            name_found=(name != "Not Found"),
            address_found=(address != "Not Found")
        )

        alert_level = get_alert_level(fraud_score)

        # Final Status
        status = "Fraud Suspected" if risk_level=="High" else "Verified"

        # Save to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kyc_records
            (name, address, status, aadhaar_hash,
             fraud_score, risk_level, alert_level,
             pin_code, pin_status, state)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                name,
                address,
                status,
                aadhaar_hash,
                fraud_score,
                risk_level,
                alert_level,
                pin,
                pin_status,
                state
            ))

        # cursor.execute("""
        #     INSERT INTO kyc_records
        #     (name, address, status, aadhaar_hash, fraud_score, risk_level, alert_level)
        #     VALUES (%s,%s,%s,%s,%s,%s,%s)
        #     """, (name, address, status, aadhaar_hash, fraud_score, risk_level, alert_level))

        conn.commit()
        conn.close()

        # Prepare latest record for template
        latest_record = {
            "name": name,
            "address": address,
            "status": status,
            "fraud_score": fraud_score,
            "alert_level": alert_level,
            "duplicate": duplicate_text,
            "masked_aadhaar": masked_text[-12:]  # last 4 digits visible
        }

    return render_template("dashboard.html", username=session["user"], latest_record=latest_record)


# CSV export Route
@app.route("/export/csv")
def export_csv():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    query = "SELECT id, name, address, status, fraud_score, risk_level, created_at FROM kyc_records"
    df = pd.read_sql(query, conn)
    conn.close()

    response = Response(
        df.to_csv(index=False),
        mimetype="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=kyc_records.csv"
    return response


# PDF export Route
@app.route("/export/pdf")
def export_pdf():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM kyc_records")
    records = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "KYC Verification Report", ln=True, align="C")

    pdf.set_font("Arial", size=10)
    pdf.ln(5)

    for r in records:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, f"Record ID: {r['id']}", ln=True)

        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Name: {clean_text(r['name'])}", ln=True)
        pdf.cell(0, 7, f"Address: {clean_text(r['address'])}", ln=True)
        pdf.cell(0, 7, f"Status: {clean_text(r['status'])}", ln=True)
        pdf.cell(0, 7, f"Fraud Score: {r['fraud_score']}", ln=True)
        pdf.cell(0, 7, f"Risk Level: {clean_text(r['risk_level'])}", ln=True)
        pdf.cell(0, 7, f"Date: {r['created_at']}", ln=True)
        pdf.ln(4)

    response = Response(
        pdf.output(dest="S").encode("latin-1"),
        mimetype="application/pdf"
    )
    response.headers["Content-Disposition"] = "attachment; filename=kyc_report.pdf"
    return response


# alert Route
@app.route("/alerts")
def get_alerts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, fraud_score, alert_level
        FROM kyc_records
        ORDER BY created_at DESC LIMIT 5
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)









# Data verify route
@app.route("/verify", methods=["POST"])
def verify():
    file = request.files["aadhaar"]
    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    if is_blurry(path):
        return render_template(
            "result.html",
            status="Rejected",
            name="N/A",
            address="Image too blurry",
            text="Please upload a clear document image"
        )

    extracted_text = extract_text(path)

    # Mask data
    masked_text = mask_aadhaar(extracted_text)

    # Aadhaar hash
    aadhaar_hash = extract_and_hash_aadhaar(extracted_text)

    # Duplicate check
    duplicate = is_duplicate(aadhaar_hash)

    # Parse name & address
    name, address = extract_name_address(masked_text)

    # Fraud decision
    if duplicate:
        status = "Fraud Suspected (Duplicate Aadhaar)"
    else:
        status = fraud_check(masked_text)
    
    is_name_found = name != "Not Found"
    is_address_found = address != "Not Found"

    # Fraud score calculation
    fraud_score, risk_level = calculate_fraud_score(
        is_duplicate=duplicate,
        is_blurry=is_blurry(path),
        text_length=len(masked_text),
        name_found=is_name_found,
        address_found=is_address_found
    )

    # Final status
    if risk_level == "High":
        status = "Fraud Suspected"
    else:
        status = "Verified"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO kyc_records
       (name, address, status, aadhaar_hash, fraud_score, risk_level)
       VALUES (%s,%s,%s,%s,%s,%s)""",
        (name, address, status, aadhaar_hash, fraud_score, risk_level)
    )
  
    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        status=status,
        name=name,
        address=address,
        fraud_score=fraud_score,
        risk_level=risk_level,
        text=masked_text
    )


if __name__ == "__main__":
    app.run(debug=True)
