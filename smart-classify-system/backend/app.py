from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import os
import json
import random
import time
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
from classifier import analyze_document_with_highlighting, allowed_file
from fpdf import FPDF
import feedback_system 

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Files & Storage ---
USERS_FILE = 'users.json'
HISTORY_FILE = 'history.json'
otp_storage = {}
temp_signup_data = {}

# --- Helpers ---
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_simulation(contact, method, otp_code):
    print(f"\n[OTP] Sending to {contact}: {otp_code}\n")
    return True

# --- Main Routes ---
@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        password = request.form.get('password')
        
        # Admin Backdoor
        if user_input == "admin" and password == "admin123":
            session['user'] = "admin"; session['role'] = "admin"
            return redirect(url_for('admin_users'))

        users = load_json(USERS_FILE)
        found = False
        for u in users.values():
            if (u.get('username')==user_input or u.get('email')==user_input or u.get('phone')==user_input) and u.get('password')==password:
                session['user'] = u.get('username')
                session['role'] = u.get('role', 'user')
                found = True; break
        
        if found:
            if session['role'] == 'admin': return redirect(url_for('admin_users'))
            return redirect(url_for('main'))
        else:
            flash("Invalid username/password.", "error")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name'); username = request.form.get('username')
        email = request.form.get('email'); phone = request.form.get('phone')
        password = request.form.get('password'); confirm = request.form.get('confirm_password')
        method = request.form.get('verify_method')

        if password != confirm: flash("Passwords mismatch", "error"); return redirect(url_for('signup'))
        users = load_json(USERS_FILE)
        for u in users.values():
            if u.get('username') == username: flash("Username taken", "error"); return redirect(url_for('signup'))

        otp = generate_otp()
        target = email if method == 'email' else phone
        temp_signup_data[target] = {"name": name, "username": username, "email": email, "phone": phone, "password": password, "role": "user"}
        otp_storage[target] = {"code": otp, "time": time.time()}
        
        send_otp_simulation(target, method, otp)
        flash(f"OTP Sent! (Demo Code: {otp})", "success")
        return redirect(url_for('verify_otp', contact=target, context='signup', method=method))
    return render_template('signup.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        contact = request.form.get('contact'); method = request.form.get('method')
        users = load_json(USERS_FILE); exists = False
        for u in users.values():
            if (method=='email' and u.get('email')==contact) or (method=='phone' and u.get('phone')==contact): exists=True; break
        if contact=="admin@system.com": exists=True
        
        if exists:
            otp = generate_otp(); otp_storage[contact]={"code":otp, "time":time.time()}
            send_otp_simulation(contact, method, otp)
            flash(f"OTP Sent! (Demo Code: {otp})", "success")
            return redirect(url_for('verify_otp', contact=contact, context='reset', method=method))
        else: flash("User not found", "error")
    return render_template('forgot_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    contact = request.args.get('contact'); context = request.args.get('context'); method = request.args.get('method')
    if request.method == 'POST':
        otp = request.form.get('otp'); key = request.form.get('contact_key'); ctype = request.form.get('context_type')
        record = otp_storage.get(key)
        if record and record['code'] == otp:
            del otp_storage[key]
            if ctype == 'signup':
                users = load_json(USERS_FILE); users[str(len(users)+100)] = temp_signup_data[key]
                save_json(USERS_FILE, users); del temp_signup_data[key]
                flash("Verified! Login now.", "success"); return redirect(url_for('login'))
            else:
                session['reset_contact'] = key; return redirect(url_for('reset_new_password'))
        else: flash("Invalid Code", "error"); return redirect(url_for('verify_otp', contact=key, context=ctype, method=method))
    return render_template('verify_otp.html', contact=contact, context=context, method=method)

@app.route('/resend_otp')
def resend_otp():
    contact = request.args.get('contact'); method = request.args.get('method')
    otp = generate_otp(); otp_storage[contact] = {"code": otp, "time": time.time()}
    send_otp_simulation(contact, method, otp)
    flash(f"New OTP Sent! (Demo Code: {otp})", "success")
    return redirect(request.referrer)

@app.route('/reset_new_password', methods=['GET', 'POST'])
def reset_new_password():
    if 'reset_contact' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        pwd = request.form.get('password'); target = session['reset_contact']; users = load_json(USERS_FILE)
        for uid, u in users.items():
            if u.get('email')==target or u.get('phone')==target:
                users[uid]['password'] = pwd; save_json(USERS_FILE, users); session.pop('reset_contact', None)
                flash("Password Updated", "success"); return redirect(url_for('login'))
    return render_template('reset_password.html')

# --- App Core ---
@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session: return redirect(url_for('login'))
    result = None; report_id = request.args.get('report_id'); filename = None
    if report_id:
        history = load_json(HISTORY_FILE)
        if report_id in history: result = history[report_id].get('result'); filename = history[report_id].get('filename')
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename); path = os.path.join(app.config['UPLOAD_FOLDER'], filename); file.save(path)
            result = analyze_document_with_highlighting(path); history = load_json(HISTORY_FILE); hid = str(len(history)+1)
            history[hid] = {"user": session['user'], "filename": filename, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "result": result}
            save_json(HISTORY_FILE, history); return redirect(url_for('main', report_id=hid))
        else: flash("Invalid file", "error")
    return render_template('main.html', user=session['user'], result=result, filename=filename, report_id=report_id)

@app.route('/submit_contribution', methods=['POST'])
def submit_contribution():
    if 'user' not in session: return redirect(url_for('login'))
    feedback_system.add_submission(request.form.get('text'), request.form.get('type'), request.form.get('system_type'), session['user'])
    flash("Contribution Submitted!", "success")
    return redirect(request.referrer or url_for('main'))

@app.route('/user/history')
def user_history():
    if 'user' not in session: return redirect(url_for('login'))
    all_h = load_json(HISTORY_FILE); my_h = {k: v for k, v in all_h.items() if v.get('user') == session['user']}
    return render_template('user_history.html', history=my_h, user=session['user'])

# --- Admin ---
@app.route('/admin')
def admin_dashboard(): return redirect(url_for('admin_users'))

@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_users.html', users=load_json(USERS_FILE), current_admin=session['user'])

@app.route('/admin/contributions')
def admin_contributions():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    feedback_system.check_expired()
    return render_template('admin_contributions.html', submissions=feedback_system.load_submissions(), current_admin=session['user'])

@app.route('/admin/history')
def admin_history():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_history.html', history=load_json(HISTORY_FILE), current_admin=session['user'])

@app.route('/admin/add_user', methods=['POST'])
def admin_add_user():
    users = load_json(USERS_FILE)
    if any(u.get('username') == request.form.get('username') for u in users.values()): flash("Exists", "error"); return redirect(url_for('admin_users'))
    users[str(len(users)+100)] = {"name": request.form.get('name'), "username": request.form.get('username'), "email": request.form.get('email'), "password": request.form.get('password'), "role": request.form.get('role')}
    save_json(USERS_FILE, users); flash("Added", "success"); return redirect(url_for('admin_users'))

@app.route('/admin/edit_user', methods=['POST'])
def admin_edit_user():
    uid = request.form.get('user_id'); users = load_json(USERS_FILE)
    if uid in users:
        users[uid].update({"name": request.form.get('name'), "email": request.form.get('email'), "role": request.form.get('role')})
        if request.form.get('password'): users[uid]['password'] = request.form.get('password')
        save_json(USERS_FILE, users); flash("Updated", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<user_id>')
def admin_delete_user(user_id):
    users = load_json(USERS_FILE)
    if user_id in users: del users[user_id]; save_json(USERS_FILE, users); flash("Deleted", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/vote/<sub_id>/<action>')
def admin_vote(sub_id, action):
    success, msg = feedback_system.vote_submission(sub_id, session['user'], action)
    flash(msg, "success" if success else "error"); return redirect(url_for('admin_contributions'))

@app.route('/admin/train_model')
def admin_train_model():
    try: subprocess.run(["python", "train_model.py"], check=True); import classifier; import importlib; importlib.reload(classifier); classifier.classifier = classifier.RequirementClassifier(); flash("Retrained!", "success")
    except Exception as e: flash(f"Error: {e}", "error")
    return redirect(url_for('admin_contributions'))

# --- Actions ---
@app.route('/add_requirement/<report_id>', methods=['POST'])
def add_requirement(report_id):
    h = load_json(HISTORY_FILE)
    if report_id in h:
        h[report_id]['result']['requirements'].append({"requirement": request.form.get('requirement'), "type": request.form.get('type'), "confidence": 1.0})
        save_json(HISTORY_FILE, h)
    return redirect(request.referrer)

@app.route('/edit_requirement/<report_id>', methods=['POST'])
def edit_requirement(report_id):
    h = load_json(HISTORY_FILE)
    if report_id in h:
        h[report_id]['result']['requirements'][int(request.form.get('index'))]['requirement'] = request.form.get('requirement')
        save_json(HISTORY_FILE, h)
    return redirect(request.referrer)

@app.route('/delete_requirement/<report_id>', methods=['POST'])
def delete_requirement(report_id):
    h = load_json(HISTORY_FILE)
    if report_id in h:
        del h[report_id]['result']['requirements'][int(request.form.get('index'))]
        save_json(HISTORY_FILE, h)
    return redirect(request.referrer)

@app.route('/download_report/<report_id>')
def download_report(report_id):
    h = load_json(HISTORY_FILE)
    if report_id not in h: return "404", 404
    data = h[report_id]; pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"File: {data.get('filename')}", ln=True); pdf.ln(10)
    for rtype in ["Functional", "Non-Functional"]:
        pdf.cell(200, 10, txt=f"{rtype}", ln=True)
        for r in data['result']['requirements']:
            if r['type'] == rtype: pdf.multi_cell(0, 8, txt=f"- {r['requirement'].encode('latin-1','replace').decode('latin-1')}"); pdf.ln(2)
    pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], f"Report_{report_id}.pdf"))
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], f"Report_{report_id}.pdf"), as_attachment=True)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

if __name__ == '__main__': app.run(debug=True)