import bcrypt
import MySQLdb

# Koneksi ke database
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="",
    db="smart_facility_db"
)

cursor = db.cursor()

# Password admin
password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Hapus admin lama
cursor.execute("DELETE FROM users WHERE username = 'admin'")

# Buat admin baru
sql = f"INSERT INTO users (username, password, role, nama_lengkap, email) VALUES ('admin', '{hashed.decode('utf-8')}', 'admin', 'Administrator', 'admin@kampus.ac.id')"
cursor.execute(sql)

db.commit()
db.close()

print("=" * 50)
print("✅ ADMIN BERHASIL DIBUAT!")
print("=" * 50)
print("Username: admin")
print("Password: admin123")
print("=" * 50)