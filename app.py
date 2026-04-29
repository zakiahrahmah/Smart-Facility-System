from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import hashlib
from datetime import datetime
import pymysql
import os

app = Flask(__name__)

# ================== CONFIG ==================
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bebas123')

# ================== DATABASE ==================
def get_db():
    host = os.environ.get("MYSQLHOST", "localhost")
    user = os.environ.get("MYSQLUSER", "root")
    password = os.environ.get("MYSQLPASSWORD", "")
    db = os.environ.get("MYSQLDATABASE", "smart_facility_db")

    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        cursorclass=pymysql.cursors.DictCursor
    )

# ================== PASSWORD ==================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

# ================== LOGIN ==================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role, nama_lengkap):
        self.id = id
        self.username = username
        self.role = role
        self.nama_lengkap = nama_lengkap

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, role, nama_lengkap FROM users WHERE id=%s",
            (user_id,)
        )
        user = cursor.fetchone()

        conn.close()

        if user:
            return User(user['id'], user['username'], user['role'], user['nama_lengkap'])

    except Exception as e:
        print("USER LOAD ERROR:", e)

    return None

# ================== CONTEXT ==================
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ================== ROUTES ==================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username=%s",
                (username,)
            )
            user = cursor.fetchone()

            conn.close()

            if user and check_password(password, user['password']):
                user_obj = User(user['id'], user['username'], user['role'], user['nama_lengkap'])
                login_user(user_obj)

                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))

            flash('Username atau password salah!', 'danger')

    except Exception as e:
        print("LOGIN ERROR:", e)
        return f"LOGIN ERROR: {str(e)}"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama_lengkap']
        username = request.form['username']
        email = request.form['email']
        password = hash_password(request.form['password'])

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing = cursor.fetchone()

        if existing:
            flash("Username sudah digunakan!", "danger")
        else:
            cursor.execute("""
                INSERT INTO users (nama_lengkap, username, email, password, role)
                VALUES (%s, %s, %s, %s, 'user')
            """, (nama, username, email, password))

            conn.commit()
            conn.close()

            flash("Registrasi berhasil, silakan login!", "success")
            return redirect(url_for('login'))

        conn.close()

    return render_template("register.html")

@app.route('/fasilitas')
@login_required
def fasilitas():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fasilitas")
    data = cursor.fetchall()

    conn.close()

    return render_template("fasilitas.html", data=data)

# ================== DASHBOARD ==================
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM fasilitas WHERE status='tersedia'")
        fasilitas = cursor.fetchall()

        cursor.execute("""
            SELECT p.*, f.nama_fasilitas
            FROM peminjaman p
            JOIN fasilitas f ON p.fasilitas_id=f.id
            WHERE p.user_id=%s
        """, (current_user.id,))
        riwayat = cursor.fetchall()

        conn.close()

        return render_template(
            'dashboard.html',
            fasilitas=fasilitas,
            riwayat=riwayat
        )

    except Exception as e:
        print("DASHBOARD ERROR:", e)
        return f"ERROR: {str(e)}"

# ================== TEST DB ==================
@app.route('/cekdb')
def cekdb():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return "DB CONNECT OK"
    except Exception as e:
        return f"DB ERROR: {str(e)}"

# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)