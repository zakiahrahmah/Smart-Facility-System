import bcrypt
import MySQLdb

# Sesuaikan koneksi database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    password='',  # Kosongkan jika pakai XAMPP default
    database='smart_facility_db'
)

cursor = conn.cursor()

# Data admin baru
username = 'admin'
password = 'admin123'
nama_lengkap = 'Administrator'
email = 'admin@example.com'

# Hash password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

try:
    # Insert admin baru
    cursor.execute("""
        INSERT INTO users (username, password, role, nama_lengkap, email) 
        VALUES (%s, %s, 'admin', %s, %s)
    """, (username, hashed_password, nama_lengkap, email))
    
    conn.commit()
    print("\n✅ ADMIN BERHASIL DITAMBAHKAN!")
    print("========================")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Role: admin")
    print("========================")
    print("\nSilakan login ke aplikasi sekarang!")
    
except Exception as e:
    print(f"❌ Gagal menambahkan admin: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
    