from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import hashlib
from datetime import datetime
import MySQLdb.cursors
import os
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# ================== KONFIG DATABASE (FIX UNTUK HOSTING) ==================
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'smart_facility_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret123')

mysql = MySQL(app)

# ================== HASH PASSWORD ==================
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, username, role, nama_lengkap FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user['id'], user['username'], user['role'], user['nama_lengkap'])
    return None

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ================== ROUTES ==================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password(password, user['password']):
            user_obj = User(user['id'], user['username'], user['role'], user['nama_lengkap'])
            login_user(user_obj)

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM fasilitas WHERE status = 'tersedia'")
    fasilitas = cursor.fetchall()

    cursor.execute("""
        SELECT p.*, f.nama_fasilitas
        FROM peminjaman p
        JOIN fasilitas f ON p.fasilitas_id = f.id
        WHERE p.user_id = %s
    """, (current_user.id,))
    riwayat = cursor.fetchall()

    cursor.close()

    return render_template('dashboard.html', fasilitas=fasilitas, riwayat=riwayat)

# ================== RUN APP ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))