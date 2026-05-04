from flask import Flask, render_template, request, redirect, url_for, flash, session 
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
    return pymysql.connect(
        host=os.environ["MYSQLHOST"],
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"],
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

# ================== LOGIN ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
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

# ================== REGISTER ==================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
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
                return render_template("register.html")

            cursor.execute("""
                INSERT INTO users (nama_lengkap, username, email, password, role)
                VALUES (%s, %s, %s, %s, 'user')
            """, (nama, username, email, password))

            conn.commit()
            conn.close()

            flash("Registrasi berhasil!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            print("REGISTER ERROR:", e)
            return f"REGISTER ERROR: {str(e)}"

    return render_template("register.html")

# ================== DASHBOARD USER ==================
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM fasilitas")
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

# ================== PINJAM ==================
@app.route('/pinjam', methods=['POST'])
@login_required
def pinjam():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO peminjaman 
            (user_id, fasilitas_id, jumlah, tanggal_pinjam, waktu_mulai, waktu_selesai, keterangan, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')
        """, (
            current_user.id,
            request.form['fasilitas_id'],
            request.form['jumlah'],
            request.form['tanggal'],
            request.form['waktu_mulai'],
            request.form['waktu_selesai'],
            request.form['keterangan']
        ))

        conn.commit()
        conn.close()

        flash("Peminjaman berhasil!", "success")
        return redirect(url_for('dashboard'))

    except Exception as e:
        return f"PINJAM ERROR: {str(e)}"

# ================== ADMIN ==================
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Statistik
        cursor.execute("SELECT COUNT(*) as total FROM peminjaman WHERE status='pending'")
        pending = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM peminjaman WHERE status='disetujui'")
        disetujui = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM fasilitas")
        total_fasilitas = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='user'")
        total_mahasiswa = cursor.fetchone()['total']

        # Data peminjaman pending
        cursor.execute("""
        SELECT p.*, u.username, u.nama_lengkap, f.nama_fasilitas
        FROM peminjaman p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN fasilitas f ON p.fasilitas_id = f.id
         WHERE p.status = 'pending'
    """)
        peminjaman_pending = cursor.fetchall()

        conn.close()

        return render_template(
            "admin_dashboard.html",
            pending=pending,
            disetujui=disetujui,
            total_fasilitas=total_fasilitas,
            total_mahasiswa=total_mahasiswa,
            peminjaman_pending=peminjaman_pending
        )

    except Exception as e:
        return f"ADMIN ERROR: {str(e)}"

@app.route('/update_status/<int:id>/<status>')
@login_required
def update_status(id, status):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE peminjaman 
            SET status=%s 
            WHERE id=%s
        """, (status, id))

        conn.commit()
        conn.close()

        flash("Status berhasil diperbarui!", "success")
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        return f"UPDATE ERROR: {str(e)}"
    
@app.route('/batal_peminjaman/<int:id>', methods=['POST'])
@login_required
def batal_peminjaman(id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Cek status peminjaman
        cursor.execute("SELECT status FROM peminjaman WHERE id = %s AND user_id = %s", (id, current_user.id))
        data = cursor.fetchone()

        if data:
            status = data['status']

            if status == 'pending':
                cursor.execute("UPDATE peminjaman SET status='dibatalkan' WHERE id=%s", (id,))
                conn.commit()
                flash('Peminjaman berhasil dibatalkan!', 'success')
            else:
                flash('Peminjaman tidak bisa dibatalkan!', 'danger')

        conn.close()
        return redirect(url_for('dashboard'))

    except Exception as e:
        return f"BATAL ERROR: {str(e)}"
    
# ================== LOGOUT ==================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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