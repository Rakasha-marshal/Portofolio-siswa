import hashlib
import sqlite3
import streamlit as st

# --- 1. INISIALISASI DATABASE & FUNGSI LOGIKA ---
DB_NAME = "portofolio.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  # Tabel Portofolio
  c.execute("""
        CREATE TABLE IF NOT EXISTS portofolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kategori TEXT NOT NULL,
            deskripsi TEXT NOT NULL,
            link_karya TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)
  # Tabel User Admin (Default admin / password: password123)
  c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
  # Masukkan akun default jika belum ada (admin / password123)
  default_pass = hashlib.sha256("password123".encode()).hexdigest()
  c.execute(
      "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
      ("admin", default_pass),
  )
  conn.commit()
  conn.close()


def get_data():
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute("SELECT id, nama, kategori, deskripsi, link_karya, status FROM portofolio")
  data = c.fetchall()
  conn.close()
  return data


def add_portofolio(nama, kategori, deskripsi, link_karya):
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute(
      "INSERT INTO portofolio (nama, kategori, deskripsi, link_karya, status)"
      " VALUES (?, ?, ?, ?, 'Pending')",
      (nama, kategori, deskripsi, link_karya),
  )
  conn.commit()
  conn.close()


def update_status(item_id, status):
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute(
      "UPDATE portofolio SET status = ? WHERE id = ?", (status, item_id)
  )
  conn.commit()
  conn.close()


def delete_portofolio(item_id):
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute("DELETE FROM portofolio WHERE id = ?", (item_id,))
  conn.commit()
  conn.close()


def verify_user(username, password):
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  hashed_pass = hashlib.sha256(password.encode()).hexdigest()
  c.execute(
      "SELECT * FROM users WHERE username = ? AND password = ?",
      (username, hashed_pass),
  )
  user = c.fetchone()
  conn.close()
  return user is not None


# --- 2. KONFIGURASI HALAMAN & TAMPILAN UTAMA ---
st.set_page_config(
    page_title="Portofolio Digital Siswa", page_icon="🎓", layout="wide"
)

# Jalankan inisialisasi database
init_db()

st.title("🎓 Sistem Portofolio Digital Siswa")
st.markdown(
    "Platform portofolio berbasis web untuk mengelola karya dan rekomendasi"
    " secara terstruktur."
)

# --- 3. SISTEM LOGIN ADMIN DI SIDEBAR (KEAMANAN) ---
st.sidebar.header("🔐 Panel Autentikasi")

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
  with st.sidebar.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_login = st.form_submit_button("Login Admin")

    if submit_login:
      if verify_user(username, password):
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success("Login berhasil!")
        st.rerun()
      else:
        st.error("Username atau password salah!")
  st.sidebar.info("Default Admin -> Username: `admin` | Password: `password123`")
else:
  st.sidebar.success(f"Login sebagai: **{st.session_state['username']}**")
  if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.rerun()

# --- 4. NAVIGASI UTAMA (TAB MENU) ---
tab1, tab2 = st.tabs(["📂 Lihat Portofolio", "➕ Tambah Portofolio Baru"])

with tab1:
  st.subheader("Daftar Portofolio Siswa")
  rows = get_data()

  if not rows:
    st.info("Belum ada data portofolio yang diunggah.")
  else:
    for row in rows:
      item_id, nama, kategori, deskripsi, link_karya, status = row
      with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
          st.markdown(f"### {nama}")
          st.write(f"**Kategori:** {kategori}")
          st.write(f"**Deskripsi:** {deskripsi}")
          st.markdown(f"🔗 [Kunjungi Tautan Karya]({link_karya})")
          st.caption(f"Status Verifikasi: **{status}**")

        with col2:
          # Kontrol khusus Admin (Keamanan & Hak Akses)
          if st.session_state["logged_in"]:
            st.markdown("#### Kontrol Admin")
            new_status = st.selectbox(
                "Ubah Status",
                ["Pending", "Disetujui", "Ditolak"],
                index=["Pending", "Disetujui", "Ditolak"].index(status),
                key=f"status_{item_id}",
            )
            if st.button("Simpan Status", key=f"save_{item_id}"):
              update_status(item_id, new_status)
              st.success("Status diperbarui!")
              st.rerun()

            if st.button("🗑️ Hapus Data", key=f"del_{item_id}"):
              delete_portofolio(item_id)
              st.warning("Data berhasil dihapus!")
              st.rerun()
          else:
            st.info("Login admin di sidebar untuk mengelola data ini.")

with tab2:
  st.subheader("Formulir Pengunggahan Portofolio")
  with st.form("form_portofolio"):
    nama_siswa = st.text_input("Nama Lengkap / Judul Karya")
    kategori_karya = st.selectbox(
        "Kategori",
        [
            "Pemrograman / Web",
            "Desain Grafis",
            "Karya Tulis Ilmiah",
            "Lainnya",
        ],
    )
    deskripsi_karya = st.text_area("Deskripsi Singkat Karya")
    link_karya = st.text_input("Tautan Karya (URL GitHub, Google Drive, dll)")

    submit_karya = st.form_submit_button("Kirim Portofolio")

    if submit_karya:
      if nama_siswa and deskripsi_karya and link_karya:
        add_portofolio(
            nama_siswa, kategori_karya, deskripsi_karya, link_karya
        )
        st.success(
            "Portofolio berhasil ditambahkan dan menunggu verifikasi admin!"
        )
      else:
        st.error("Mohon lengkapi semua kolom yang tersedia.")
