"""
============================================================
 PREDICTIVE MAINTENANCE - IoT CVT MOTOR NMAX
 Web Dashboard menggunakan Streamlit + Firebase Admin
============================================================
 Deskripsi:
 Dashboard real-time untuk memantau kondisi mesin/CVT motor
 NMAX berdasarkan data getaran dan suara dari sensor IoT.
 Dilengkapi sistem alerting via email otomatis.
============================================================
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import plotly.graph_objects as go
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from collections import deque
import joblib
import os

# ============================================================
#  KONFIGURASI HALAMAN STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Predictive Maintenance - CVT NMAX",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#  CUSTOM CSS - Tampilan Profesional & Modern
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    :root { --card-bg: rgba(18,20,36,0.6); --card-border: rgba(255,255,255,0.08); }
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .main-header { background: linear-gradient(-45deg, #0f172a, #1e1b4b, #0c4a6e, #172554);
        background-size: 400% 400%; animation: gradBG 15s ease infinite;
        border: 1px solid var(--card-border); border-radius: 20px;
        padding: 35px 40px; margin-bottom: 30px; position: relative; overflow: hidden;
        box-shadow: 0 10px 30px -10px rgba(14,165,233,0.3); }
    @keyframes gradBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
    .main-header::after { content:''; position:absolute; top:0; left:-100%; width:50%; height:100%;
        background:linear-gradient(to right,transparent,rgba(255,255,255,0.05),transparent);
        transform:skewX(-20deg); animation:shine 6s infinite; }
    @keyframes shine { 0%{left:-100%} 20%{left:200%} 100%{left:200%} }
    .main-header h1 { color:#fff; font-size:2.2rem; font-weight:800; margin:0 0 8px; text-shadow:0 2px 10px rgba(0,0,0,0.5); }
    .main-header p { color:#cbd5e1; font-size:1.05rem; margin:0; opacity:0.9; }
    .metric-card { background: var(--card-bg); backdrop-filter: blur(12px);
        border: 1px solid var(--card-border); border-radius: 20px;
        padding: 30px 24px; text-align: center; position: relative; overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:4px;
        background:linear-gradient(90deg,#0ea5e9,#8b5cf6); opacity:0; transition:opacity 0.3s; }
    .metric-card:hover { transform:translateY(-8px) scale(1.02); border-color:rgba(255,255,255,0.2);
        box-shadow:0 15px 40px rgba(14,165,233,0.2); }
    .metric-card:hover::before { opacity:1; }
    .metric-card .label { color:#94a3b8; font-size:0.9rem; font-weight:600; text-transform:uppercase;
        letter-spacing:2px; margin-bottom:12px; }
    .metric-card .value { font-size:3.5rem; font-weight:800; letter-spacing:-2px; line-height:1.1; margin-bottom:8px; }
    .metric-card .unit { color:#64748b; font-size:0.85rem; background:rgba(0,0,0,0.3);
        padding:4px 12px; border-radius:20px; display:inline-block; }
    .value-normal { color:#10b981; text-shadow:0 0 15px rgba(16,185,129,0.4); }
    .value-warning { color:#f59e0b; text-shadow:0 0 15px rgba(245,158,11,0.4); }
    .value-danger { color:#ef4444; text-shadow:0 0 20px rgba(239,68,68,0.6); animation:pulseV 1.5s infinite; }
    @keyframes pulseV { 0%,100%{transform:scale(1)} 50%{transform:scale(1.05)} }
    .status-badge { display:inline-flex; align-items:center; gap:8px; padding:8px 20px;
        border-radius:30px; font-size:0.9rem; font-weight:700; text-transform:uppercase;
        letter-spacing:1.5px; box-shadow:0 4px 15px rgba(0,0,0,0.2); }
    .status-normal { background:linear-gradient(135deg,rgba(16,185,129,0.2),rgba(16,185,129,0.05));
        color:#34d399; border:1px solid rgba(16,185,129,0.3); }
    .status-danger { background:linear-gradient(135deg,rgba(239,68,68,0.2),rgba(239,68,68,0.05));
        color:#f87171; border:1px solid rgba(239,68,68,0.5); animation:dangerGlow 1.5s infinite alternate; }
    @keyframes dangerGlow { from{box-shadow:0 0 10px rgba(239,68,68,0.2)} to{box-shadow:0 0 25px rgba(239,68,68,0.6)} }
    .chart-container { background:var(--card-bg); backdrop-filter:blur(12px);
        border:1px solid var(--card-border); border-radius:20px; padding:24px; margin-bottom:20px;
        box-shadow:0 8px 32px rgba(0,0,0,0.2); transition:border-color 0.3s; }
    .chart-container:hover { border-color:rgba(255,255,255,0.15); }
    .chart-title { color:#f8fafc; font-size:1.1rem; font-weight:600; margin-bottom:16px;
        display:flex; align-items:center; gap:10px; padding-bottom:12px; border-bottom:1px solid var(--card-border); }
    section[data-testid="stSidebar"] { background:rgba(10,15,30,0.8)!important; backdrop-filter:blur(15px);
        border-right:1px solid var(--card-border); }
    .stAlert > div { border-radius:16px; }
    #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
    .custom-divider { height:2px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent); margin:20px 0; }
    .live-indicator { display:inline-block; width:8px; height:8px; background:#10b981;
        border-radius:50%; margin-right:8px; box-shadow:0 0 10px #10b981; animation:blink 1s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
    @keyframes smoothGauge {
        0% { stroke-dashoffset: var(--gauge-prev); }
        100% { stroke-dashoffset: var(--gauge-curr); }
    }
    .gauge-animated-path {
        stroke-dasharray: 100;
        animation: smoothGauge 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards;
    }
    /* === SOUND-SPECIFIC STYLES === */
    .sound-card { background: linear-gradient(135deg, rgba(88,28,135,0.3), rgba(124,58,237,0.1));
        backdrop-filter: blur(12px); border: 1px solid rgba(167,139,250,0.2); border-radius: 20px;
        padding: 30px 24px; text-align: center; position: relative; overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275); box-shadow: 0 8px 32px rgba(88,28,135,0.3); }
    .sound-card::before { content:''; position:absolute; top:0; left:0; right:0; height:4px;
        background:linear-gradient(90deg,#8b5cf6,#f97316); opacity:1; }
    .sound-card:hover { transform:translateY(-8px) scale(1.02); border-color:rgba(167,139,250,0.4);
        box-shadow:0 15px 40px rgba(139,92,246,0.3); }
    .sound-card .label { color:#c4b5fd; font-size:0.9rem; font-weight:600; text-transform:uppercase;
        letter-spacing:2px; margin-bottom:12px; }
    .sound-card .value { font-size:3.5rem; font-weight:800; letter-spacing:-2px; line-height:1.1; margin-bottom:4px;
        color:#e9d5ff; text-shadow:0 0 20px rgba(139,92,246,0.5); }
    .sound-card .db-value { font-size:1.4rem; font-weight:600; color:#a78bfa; margin-bottom:8px; }
    .sound-card .unit { color:#7c3aed; font-size:0.85rem; background:rgba(139,92,246,0.15);
        padding:4px 12px; border-radius:20px; display:inline-block; }
    .vu-bar-bg { background:rgba(0,0,0,0.4); border-radius:8px; height:18px; width:100%;
        overflow:hidden; position:relative; box-shadow:inset 0 2px 4px rgba(0,0,0,0.3); }
    @keyframes vuFill { from{width:var(--vu-prev)} to{width:var(--vu-curr)} }
    .vu-bar-fill { height:100%; border-radius:8px; transition:width 0.8s ease;
        animation: vuFill 1s ease forwards;
        box-shadow:0 0 12px var(--vu-glow); position:relative; }
    .vu-bar-fill::after { content:''; position:absolute; top:0; right:0; width:3px; height:100%;
        background:rgba(255,255,255,0.8); border-radius:2px; box-shadow:0 0 8px rgba(255,255,255,0.6); }
    .vu-segments { display:flex; gap:2px; height:24px; align-items:flex-end; }
    .vu-seg { flex:1; border-radius:2px; min-width:4px; transition:height 0.3s ease, opacity 0.3s; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  INISIALISASI FIREBASE ADMIN SDK
# ============================================================
# Pastikan file serviceAccountKey.json ada di folder yang sama
# File ini didownload dari Firebase Console > Project Settings >
# Service Accounts > Generate New Private Key

@st.cache_resource
def init_firebase():
    """Inisialisasi koneksi Firebase (hanya sekali)"""
    if not firebase_admin._apps:
        try:
            # Prioritas 1: Baca dari Streamlit Secrets (Untuk Cloud Hosting)
            key_dict = dict(st.secrets["firebase_service_account"])
            cred = credentials.Certificate(key_dict)
        except Exception:
            # Prioritas 2: Baca dari file lokal (Untuk Dev/Testing Lokal)
            cred = credentials.Certificate("kerusakanmotor-3dea8-firebase-adminsdk-fbsvc-44d1f159ad.json")
            
        firebase_admin.initialize_app(cred, {
            "databaseURL": st.secrets["firebase_database_url"]
        })
    return db.reference("/Sensor")

# ============================================================
#  LOAD MODEL AI (SVM)
# ============================================================
@st.cache_resource
def load_ai_model():
    """Memuat model AI dan Scaler yang sudah dilatih"""
    model_path = 'otak_mesin_nmax.joblib'
    scaler_path = 'scaler.joblib'
    
    model = None
    scaler = None
    
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        
    return model, scaler

# ============================================================
#  FUNGSI PENGIRIMAN EMAIL PERINGATAN
# ============================================================
def kirim_email_peringatan(nilai_getaran):
    """
    Mengirim email peringatan saat getaran melebihi batas aman.
    Password diambil dari st.secrets untuk keamanan.
    """
    try:
        # Ambil konfigurasi email dari secrets.toml
        pengirim = st.secrets["email_address"]
        password = st.secrets["email_password"]
        penerima = st.secrets["email_recipient"]

        # Buat konten email
        subjek = "⚠️ PERINGATAN: Anomali Getaran Terdeteksi - CVT NMAX"
        waktu = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        body_html = f"""
        <html><body style="font-family:Arial,sans-serif; background:#f8f9fa; padding:20px;">
        <div style="max-width:500px; margin:auto; background:white; border-radius:12px;
                    border-top:4px solid #ef4444; padding:30px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color:#ef4444; margin-top:0;">⚠️ Anomali Terdeteksi!</h2>
            <p style="color:#374151;">Sistem Predictive Maintenance mendeteksi
            <strong>getaran abnormal</strong> pada CVT Motor NMAX Anda.</p>
            <table style="width:100%; border-collapse:collapse; margin:16px 0;">
                <tr style="background:#fef2f2;">
                    <td style="padding:10px; border:1px solid #fecaca; font-weight:bold;">Nilai Getaran</td>
                    <td style="padding:10px; border:1px solid #fecaca; color:#ef4444;
                        font-weight:bold; font-size:1.2em;">{nilai_getaran:.3f} G</td>
                </tr>
                <tr>
                    <td style="padding:10px; border:1px solid #e5e7eb;">Batas Normal</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">≤ 2.0 G</td>
                </tr>
                <tr style="background:#f9fafb;">
                    <td style="padding:10px; border:1px solid #e5e7eb;">Waktu Deteksi</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{waktu}</td>
                </tr>
            </table>
            <p style="color:#6b7280; font-size:0.85em;">Segera periksa kondisi mesin/CVT motor Anda
            untuk mencegah kerusakan lebih lanjut.</p>
        </div>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subjek
        msg["From"] = pengirim
        msg["To"] = penerima
        msg.attach(MIMEText(body_html, "html"))

        # Kirim via SMTP Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(pengirim, password)
            server.sendmail(pengirim, penerima, msg.as_string())

        return True
    except Exception as e:
        st.sidebar.error(f"Gagal kirim email: {e}")
        return False

# ============================================================
#  FUNGSI MEMBUAT GRAFIK PLOTLY
# ============================================================
def buat_grafik_getaran(data_waktu, data_nilai, batas=2.0):
    fig = go.Figure()
    v, t = list(data_nilai), list(data_waktu)
    fig.add_trace(go.Scatter(x=t, y=v, mode='lines', line=dict(color='rgba(0,0,0,0)', width=0),
        fill='tozeroy', fillcolor='rgba(59,130,246,0.06)', showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=t, y=v, mode='lines+markers', name='G-Force',
        line=dict(color='#60a5fa', width=3, shape='spline'),
        marker=dict(size=6, color='#60a5fa', line=dict(width=2, color='#1e3a5f')),
        hovertemplate='<b>%{y:.3f} G</b><br>%{x}<extra></extra>'))
    fig.add_hline(y=batas, line_dash="dot", line_color="#ef4444", line_width=2,
        annotation_text=f"Batas ({batas} G)", annotation_position="top left",
        annotation_font=dict(color="#f87171", size=12, family="Outfit"))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit", color="#94a3b8"), height=300, margin=dict(l=35,r=15,t=10,b=30),
        xaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False, title=None),
        yaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False, title=None, rangemode='tozero'),
        showlegend=False, hoverlabel=dict(bgcolor='#1e293b', font_size=13, bordercolor='#3b82f6'))
    return fig

def buat_grafik_suara(data_waktu, data_nilai):
    """Grafik suara menggunakan BAR CHART - tampilan berbeda dari getaran"""
    fig = go.Figure()
    v, t = list(data_nilai), list(data_waktu)
    # Warna bar berdasarkan level
    colors = []
    for val in v:
        if val > 3000:
            colors.append('#ef4444')
        elif val > 2000:
            colors.append('#f59e0b')
        elif val > 1000:
            colors.append('#a78bfa')
        else:
            colors.append('#8b5cf6')
    fig.add_trace(go.Bar(x=t, y=v, name='Suara',
        marker=dict(color=colors, line=dict(width=0),
            opacity=0.85),
        hovertemplate='<b>%{y}</b><br>%{x}<extra></extra>'))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit", color="#94a3b8"), height=300, margin=dict(l=35,r=15,t=10,b=30),
        xaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False, title=None),
        yaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False, title=None, rangemode='tozero'),
        showlegend=False, bargap=0.15,
        hoverlabel=dict(bgcolor='#1e293b', font_size=13, bordercolor='#8b5cf6'))
    return fig

def buat_gauge(nilai, nilai_sebelumnya, maks, label, warna, iterasi, format_str):
    """Gauge semi-circle - HANYA untuk getaran"""
    val_curr = max(0, min(nilai, maks))
    val_prev = max(0, min(nilai_sebelumnya, maks))
    percent_curr = (val_curr / maks) * 100
    percent_prev = (val_prev / maks) * 100
    offset_curr = 100 - percent_curr
    offset_prev = 100 - percent_prev
    formatted_val = format_str.format(nilai)
    
    html = f"""<div style="display: flex; justify-content: center; align-items: center; width: 100%; padding: 10px 0;">
<svg viewBox="0 0 100 60" style="width: 100%; max-width: 250px; overflow: visible;">
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="12" stroke-linecap="round" pathLength="100" />
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="rgba(0,0,0,0.2)" stroke-width="12" stroke-linecap="round" pathLength="100" transform="translate(0,1)" />
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="{warna}" stroke-width="12" stroke-linecap="round" pathLength="100" class="gauge-animated-path" style="--gauge-prev: {offset_prev}; --gauge-curr: {offset_curr}; filter: drop-shadow(0px 0px 8px {warna});" />
<text x="50" y="44" text-anchor="middle" font-family="'Outfit', sans-serif" font-weight="800" font-size="22" fill="#ffffff">{formatted_val}</text>
<text x="50" y="58" text-anchor="middle" font-family="'Outfit', sans-serif" font-weight="600" font-size="9" fill="#94a3b8" letter-spacing="1.5">{label}</text>
</svg>
</div>"""
    return html

def buat_vu_meter(nilai, nilai_sebelumnya, maks, db_val):
    """VU Meter horizontal bar - HANYA untuk suara (tampilan berbeda dari gauge getaran)"""
    persen_curr = max(0, min((nilai / maks) * 100, 100))
    persen_prev = max(0, min((nilai_sebelumnya / maks) * 100, 100))
    
    # Tentukan warna gradient berdasarkan level
    if persen_curr > 73:  # > 3000
        gradient = 'linear-gradient(90deg, #8b5cf6, #f59e0b, #ef4444)'
        glow = '#ef4444'
        level_text = '🔴 TINGGI'
        level_color = '#ef4444'
    elif persen_curr > 49:  # > 2000
        gradient = 'linear-gradient(90deg, #8b5cf6, #f59e0b)'
        glow = '#f59e0b'
        level_text = '🟡 SEDANG'
        level_color = '#f59e0b'
    else:
        gradient = 'linear-gradient(90deg, #8b5cf6, #a78bfa)'
        glow = '#8b5cf6'
        level_text = '🟢 NORMAL'
        level_color = '#10b981'
    
    # Generate segmen VU meter (20 bar)
    num_segments = 20
    active_segs = int((persen_curr / 100) * num_segments)
    segments_html = ''
    for i in range(num_segments):
        seg_pct = (i / num_segments) * 100
        if i < active_segs:
            if seg_pct > 73:
                seg_color = '#ef4444'
            elif seg_pct > 49:
                seg_color = '#f59e0b'
            else:
                seg_color = '#8b5cf6'
            seg_opacity = '1'
            seg_height = '100%'
        else:
            seg_color = 'rgba(255,255,255,0.05)'
            seg_opacity = '0.3'
            seg_height = '60%'
        segments_html += f'<div class="vu-seg" style="background:{seg_color}; opacity:{seg_opacity}; height:{seg_height};"></div>'
    
    html = f"""
    <div style="padding: 15px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="color:#c4b5fd; font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:1.5px;">🔊 VU METER</span>
            <span style="color:{level_color}; font-size:0.8rem; font-weight:700;">{level_text}</span>
        </div>
        <div class="vu-segments" style="height:32px; margin-bottom:12px;">
            {segments_html}
        </div>
        <div class="vu-bar-bg">
            <div class="vu-bar-fill" style="width:{persen_curr}%; background:{gradient}; --vu-prev:{persen_prev}%; --vu-curr:{persen_curr}%; --vu-glow:{glow};"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:10px; align-items:center;">
            <span style="color:#64748b; font-size:0.75rem;">0</span>
            <span style="color:#e9d5ff; font-size:1.5rem; font-weight:800;">{db_val:.1f} <span style="font-size:0.7rem; color:#a78bfa;">dB</span></span>
            <span style="color:#64748b; font-size:0.75rem;">4095</span>
        </div>
    </div>
    """
    return html

# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🏍️ Predictive Maintenance")
    st.markdown("**CVT Motor NMAX**")
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### ⚙️ Pengaturan")

    # Batas getaran (threshold)
    batas_getaran = st.slider(
        "Batas Getaran Bahaya (G)",
        min_value=0.5, max_value=5.0, value=2.0, step=0.1,
        help="Jika getaran melebihi nilai ini, sistem akan mengirim peringatan."
    )

    # Interval refresh
    interval_refresh = st.slider(
        "Interval Refresh (detik)",
        min_value=1, max_value=10, value=2, step=1,
        help="Seberapa sering dashboard memperbarui data."
    )

    # Jumlah data di grafik
    max_data_grafik = st.slider(
        "Jumlah Data di Grafik",
        min_value=10, max_value=100, value=30, step=5,
        help="Berapa banyak titik data yang ditampilkan di grafik."
    )

    # Toggle email
    aktifkan_email = st.toggle("📧 Aktifkan Notifikasi Email", value=False)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### 📋 Informasi Sensor")
    st.markdown("""
    | Sensor | Fungsi |
    |--------|--------|
    | MPU6050 | Getaran (G-Force) |
    | MAX9814 | Level Suara |
    """)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.caption("© 2026 Predictive Maintenance IoT")

# ============================================================
#  KONTEN UTAMA DASHBOARD
# ============================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>🏍️ Predictive Maintenance Dashboard</h1>
    <p>Pemantauan Kondisi Mesin &amp; CVT Motor NMAX Secara Real-Time</p>
</div>
""", unsafe_allow_html=True)

# Inisialisasi Firebase
try:
    ref_sensor = init_firebase()
except Exception as e:
    st.error(f"❌ Gagal terhubung ke Firebase: {e}")
    st.info("Pastikan file `serviceAccountKey.json` ada dan `databaseURL` sudah benar.")
    st.stop()

# Inisialisasi session state untuk menyimpan histori data grafik
if "data_getaran" not in st.session_state:
    st.session_state.data_getaran = deque(maxlen=100)
if "data_suara" not in st.session_state:
    st.session_state.data_suara = deque(maxlen=100)
if "data_db" not in st.session_state:
    st.session_state.data_db = deque(maxlen=100)
if "data_waktu" not in st.session_state:
    st.session_state.data_waktu = deque(maxlen=100)
if "email_terkirim" not in st.session_state:
    st.session_state.email_terkirim = False
if "waktu_email_terakhir" not in st.session_state:
    st.session_state.waktu_email_terakhir = 0

# Load AI Model & Scaler
model_ai, scaler_ai = load_ai_model()

# Placeholder untuk konten yang akan di-refresh
placeholder_utama = st.empty()

# ============================================================
#  LOOP UTAMA - Auto Refresh Data
# ============================================================
iterasi = 0
while True:
    iterasi += 1
    try:
        # Ambil data terbaru dari Firebase
        data_sensor = ref_sensor.get()

        if data_sensor:
            nilai_getaran = float(data_sensor.get("getaran", 0))
            nilai_suara = int(data_sensor.get("suara", 0))
            nilai_db = float(data_sensor.get("suara_db", 0))
        else:
            nilai_getaran = 0.0
            nilai_suara = 0
            nilai_db = 0.0

        # Tambahkan ke histori
        waktu_sekarang = datetime.now().strftime("%H:%M:%S")
        st.session_state.data_getaran.append(nilai_getaran)
        st.session_state.data_suara.append(nilai_suara)
        st.session_state.data_db.append(nilai_db)
        st.session_state.data_waktu.append(waktu_sekarang)

        # --- PREDIKSI AI ---
        ai_status = "TIDAK AKTIF (Belum Training)"
        is_bahaya = nilai_getaran > batas_getaran # Default ke threshold
        keyakinan_ai = 0

        if model_ai and scaler_ai:
            try:
                # 1. Siapkan fitur
                fitur = [[nilai_getaran, nilai_suara]]
                
                # 2. Samakan skala (Scaling) - PENTING!
                fitur_scaled = scaler_ai.transform(fitur)
                
                # 3. Prediksi
                prediksi = model_ai.predict(fitur_scaled)[0]
                probabilitas = model_ai.predict_proba(fitur_scaled)[0]
                
                keyakinan_ai = max(probabilitas) * 100
                is_bahaya = (prediksi == 1)
                ai_status = "BAHAYA 🚨" if is_bahaya else "AMAN ✅"
            except Exception as e:
                ai_status = f"ERROR AI: {e}"

        # Kirim email jika bahaya dan email aktif (cooldown 60 detik)
        if is_bahaya and aktifkan_email:
            waktu_skrg = time.time()
            if waktu_skrg - st.session_state.waktu_email_terakhir > 60:
                if kirim_email_peringatan(nilai_getaran):
                    st.session_state.waktu_email_terakhir = waktu_skrg
                    st.session_state.email_terkirim = True

        # Render UI di dalam placeholder (agar bisa di-refresh)
        with placeholder_utama.container():

            # --- Baris Status ---
            if is_bahaya:
                st.markdown(
                    f"""
                    <div style="text-align:center; margin-bottom:20px;">
                        <span class="status-badge status-danger" style="font-size:0.95rem; padding:10px 22px;">
                            <span class="live-indicator" style="background:#ef4444;box-shadow:0 0 10px #ef4444;"></span> 
                            🚨 ANALISIS AI: {ai_status} ({keyakinan_ai:.1f}%) 🚨
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="text-align:center; margin-bottom:20px;">
                        <span class="status-badge status-normal">
                            <span class="live-indicator"></span> ANALISIS AI: {ai_status} ({keyakinan_ai:.1f}%)
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # --- Kartu Metrik ---
            col1, col2 = st.columns(2)

            with col1:
                warna_class = "value-danger" if is_bahaya else (
                    "value-warning" if nilai_getaran > batas_getaran * 0.75 else "value-normal"
                )
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">📳 Getaran (G-Force)</div>
                    <div class="value {warna_class}">{nilai_getaran:.3f}</div>
                    <div class="unit">G (Gravitasi) | Batas: {batas_getaran} G</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # Kartu suara dengan desain BERBEDA (purple gradient + dB)
                if nilai_suara > 3000:
                    sound_icon = '🔴'
                elif nilai_suara > 2000:
                    sound_icon = '🟡'
                else:
                    sound_icon = '🟢'

                st.markdown(f"""
                <div class="sound-card">
                    <div class="label">🔊 Level Suara</div>
                    <div class="value">{nilai_suara}</div>
                    <div class="db-value">{sound_icon} {nilai_db:.1f} dB</div>
                    <div class="unit">RMS Smoothed | ADC 12-bit</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)

            # Lacak nilai yang terakhir kali dirender di UI untuk animasi
            if 'prev_ui_getaran' not in st.session_state:
                st.session_state.prev_ui_getaran = nilai_getaran
                st.session_state.prev_ui_suara = nilai_suara

            getaran_sebelumnya = st.session_state.prev_ui_getaran
            suara_sebelumnya = st.session_state.prev_ui_suara

            # Simpan state untuk loop berikutnya
            st.session_state.prev_ui_getaran = nilai_getaran
            st.session_state.prev_ui_suara = nilai_suara

            # --- Gauge (Getaran) & VU Meter (Suara) ---
            cg1, cg2 = st.columns(2)
            with cg1:
                st.markdown('<div class="chart-container" style="padding:10px 10px 0">', unsafe_allow_html=True)
                warna_g = '#ef4444' if is_bahaya else ('#f59e0b' if nilai_getaran > batas_getaran*0.75 else '#10b981')
                st.markdown(buat_gauge(nilai_getaran, getaran_sebelumnya, 5.0, 'GETARAN (G)', warna_g, iterasi, '{:.3f}'), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with cg2:
                st.markdown('<div class="chart-container" style="padding:10px 10px 0">', unsafe_allow_html=True)
                st.markdown(buat_vu_meter(nilai_suara, suara_sebelumnya, 4095, nilai_db), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # --- Grafik Real-Time ---
            waktu_tampil = list(st.session_state.data_waktu)[-max_data_grafik:]
            getaran_tampil = list(st.session_state.data_getaran)[-max_data_grafik:]
            suara_tampil = list(st.session_state.data_suara)[-max_data_grafik:]

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown('<div class="chart-container"><div class="chart-title">📉 Riwayat Getaran</div>', unsafe_allow_html=True)
                st.plotly_chart(buat_grafik_getaran(waktu_tampil, getaran_tampil, batas_getaran), use_container_width=True, key=f'cg_{iterasi}')
                st.markdown('</div>', unsafe_allow_html=True)
            with col_chart2:
                st.markdown('<div class="chart-container"><div class="chart-title">📊 Riwayat Suara</div>', unsafe_allow_html=True)
                st.plotly_chart(buat_grafik_suara(waktu_tampil, suara_tampil), use_container_width=True, key=f'cs_{iterasi}')
                st.markdown('</div>', unsafe_allow_html=True)

            # --- Statistik Ringkasan ---
            if len(getaran_tampil) > 1:
                avg_g = sum(getaran_tampil)/len(getaran_tampil)
                max_g = max(getaran_tampil)
                min_g = min(getaran_tampil)
                avg_s = sum(suara_tampil)/len(suara_tampil)
                st.markdown(f'''
                <div class="chart-container" style="text-align:center; padding:18px;">
                    <div class="chart-title" style="justify-content:center; border:none; padding:0; margin-bottom:12px;">
                        📋 Ringkasan Statistik
                    </div>
                    <div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:10px;">
                        <div><span style="color:#64748b; font-size:0.8rem;">AVG Getaran</span><br>
                            <span style="color:#60a5fa; font-size:1.3rem; font-weight:700;">{avg_g:.3f} G</span></div>
                        <div><span style="color:#64748b; font-size:0.8rem;">MAX Getaran</span><br>
                            <span style="color:#f87171; font-size:1.3rem; font-weight:700;">{max_g:.3f} G</span></div>
                        <div><span style="color:#64748b; font-size:0.8rem;">MIN Getaran</span><br>
                            <span style="color:#34d399; font-size:1.3rem; font-weight:700;">{min_g:.3f} G</span></div>
                        <div><span style="color:#64748b; font-size:0.8rem;">AVG Suara</span><br>
                            <span style="color:#a78bfa; font-size:1.3rem; font-weight:700;">{avg_s:.0f}</span></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

            # --- Info Footer ---
            st.markdown(
                f'<p style="text-align:center; color:#475569; font-size:0.75rem; margin-top:20px;">'
                f'<span class="live-indicator"></span> Live • {waktu_sekarang} • '
                f'Refresh {interval_refresh}s</p>', unsafe_allow_html=True)

    except Exception as e:
        with placeholder_utama.container():
            st.error(f"Terjadi kesalahan: {e}")

    # Tunggu sebelum refresh berikutnya
    time.sleep(interval_refresh)
