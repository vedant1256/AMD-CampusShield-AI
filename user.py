import streamlit as st
import pandas as pd
import numpy as np
import time
import hashlib
import re
import json
import os
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image, ImageFilter
import io

try:
    from zxcvbn import zxcvbn
except ImportError:
    st.error("Please install zxcvbn library by running: pip install zxcvbn")

# --- BRIDGE SETUP (Connects User to Admin) ---
SHARED_FILE = "swarm_data.json"

def init_shared_state():
    """Initializes the shared JSON file if it doesn't exist."""
    if not os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, 'w') as f:
            json.dump({"telemetry": [], "lockdown": False}, f)

def broadcast_to_admin(action_type, threat_details):
    """Writes an event from the User to the shared JSON for the Admin to see."""
    init_shared_state()
    try:
        with open(SHARED_FILE, 'r') as f:
            data = json.load(f)
            
        new_event = {
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "node_id": f"HASH_{st.session_state.user_name.upper()[:4]}",
            "action": action_type,
            "threat": threat_details
        }
        
        data["telemetry"].insert(0, new_event) # Add to top
        data["telemetry"] = data["telemetry"][:50] # Keep last 50 events
        
        with open(SHARED_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        pass # Fail silently in demo if file is locked

def check_admin_lockdown():
    """Checks if the Admin has triggered a global DEFCON 1."""
    init_shared_state()
    try:
        with open(SHARED_FILE, 'r') as f:
            data = json.load(f)
            return data.get("lockdown", False)
    except:
        return False

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CampusShield | Student Cyber Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Bridge
init_shared_state()

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = "student@campus.edu"
if 'user_name' not in st.session_state: st.session_state.user_name = "Chhagan"
if 'login_time' not in st.session_state: st.session_state.login_time = datetime.now().strftime("%H:%M:%S")
if 'is_anomaly' not in st.session_state: st.session_state.is_anomaly = False
if 'anomaly_reason' not in st.session_state: st.session_state.anomaly_reason = ""
if 'current_device' not in st.session_state: st.session_state.current_device = "macOS"
if 'recent_scans' not in st.session_state: st.session_state.recent_scans = []
if 'messages' not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Ryzen-AI Mentor. Ask me anything about cybersecurity, campus policies, or how to secure your code!"}]
if 'badges' not in st.session_state: st.session_state.badges = ["🛡️ Privacy Rookie"]
if 'two_fa' not in st.session_state: st.session_state.two_fa = False
if 'xp_points' not in st.session_state: st.session_state.xp_points = 450
if 'daily_streak' not in st.session_state: st.session_state.daily_streak = 3

# Dashboard State
if 'dark_web_scanned' not in st.session_state: st.session_state.dark_web_scanned = False
if 'endpoint_scanned' not in st.session_state: st.session_state.endpoint_scanned = False
if 'endpoint_fixed' not in st.session_state: st.session_state.endpoint_fixed = False

# Emergency Lockdown State
if 'lockdown_mode' not in st.session_state: st.session_state.lockdown_mode = False

# Quiz State Management
if 'quiz_index' not in st.session_state: st.session_state.quiz_index = 0
if 'quiz_score' not in st.session_state: st.session_state.quiz_score = 0
if 'quiz_completed' not in st.session_state: st.session_state.quiz_completed = False
if 'show_explanation' not in st.session_state: st.session_state.show_explanation = False
if 'honeytoken' not in st.session_state: st.session_state.honeytoken = None
if 'file_sanitized' not in st.session_state: st.session_state.file_sanitized = False

# Zero-Click Integration State
if 'ext_clicked' not in st.session_state: st.session_state.ext_clicked = False
if 'ext_url' not in st.session_state: st.session_state.ext_url = ""
if 'ext_detonated' not in st.session_state: st.session_state.ext_detonated = False
if 'payload_stripped' not in st.session_state: st.session_state.payload_stripped = False
if 'ide_scanned' not in st.session_state: st.session_state.ide_scanned = False
if 'ide_patched' not in st.session_state: st.session_state.ide_patched = False

# Sync Lockdown with Admin
if check_admin_lockdown():
    st.session_state.lockdown_mode = True

# --- DYNAMIC THEME ENGINE ---
if st.session_state.lockdown_mode:
    t = { "bg": "#450a0a", "sidebar": "#220000", "primary": "#ef4444", "text": "#fca5a5", "accent": "#b91c1c", "card": "#7f1d1d" }
else:
    t = { "bg": "#0f172a", "sidebar": "#1e293b", "primary": "#10b981", "text": "#f8fafc", "accent": "#34d399", "card": "#1e293b" }

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; transition: background-color 0.5s ease; }}
    [data-testid="stSidebar"] {{ background-color: {t['sidebar']} !important; transition: background-color 0.5s ease; }}
    .stButton>button {{ border-radius: 6px; background-color: {t['primary']}; color: white; border: none; font-weight: bold; width: 100%; margin-bottom: 10px; }}
    .badge {{ padding: 5px 12px; border-radius: 15px; background: {t['primary']}22; color: {t['primary']}; font-size: 0.8rem; border: 1px solid {t['primary']}; display: inline-block; margin: 2px; }}
    h1, h2, h3 {{ color: {t['primary']}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    .ueba-card {{ border-left: 4px solid {t['primary']}; padding: 15px; background-color: {t['card']}; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .ueba-alert {{ border-left: 4px solid #ef4444; padding: 15px; background-color: #450a0a55; border-radius: 5px; margin-bottom: 20px; }}
    .feature-box {{ background-color: {t['card']}; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: background-color 0.5s ease; }}
    .email-row-safe {{ padding: 10px; border-bottom: 1px solid #444; }}
    .email-row-danger {{ padding: 10px; border-bottom: 1px solid #444; background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; }}
    .code-snippet {{ background-color: #111; padding: 15px; border-radius: 5px; font-family: monospace; color: #a5b4fc; }}
    .live-ticker {{ background-color: #020617; border-left: 4px solid #3b82f6; padding: 10px; margin-bottom: 20px; border-radius: 4px; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }}
    .xp-bar {{ width: 100%; background-color: #333; border-radius: 10px; overflow: hidden; height: 15px; margin-top: 5px; }}
    .xp-fill {{ height: 100%; background-color: #10b981; width: 65%; }}
    .auto-heal-box {{ border-left: 4px solid #3b82f6; padding: 15px; background-color: rgba(59, 130, 246, 0.1); border-radius: 5px; margin-top: 20px; }}
    .forensics-term {{ background-color: #020617; color: #10b981; font-family: 'Courier New', Courier, monospace; padding: 15px; border-radius: 5px; height: 250px; overflow-y: scroll; border: 1px solid #333; font-size: 0.9rem; }}
    .hex-col {{ color: #64748b; margin-right: 15px; user-select: none; }}
    .ascii-col {{ color: #fbbf24; margin-left: 15px; }}
    .threat-str {{ color: #ef4444; font-weight: bold; }}
    .stripper-flow {{ display: flex; justify-content: space-between; align-items: center; background-color: #111; padding: 20px; border-radius: 10px; border: 1px dashed #444; }}
    .flow-box {{ text-align: center; padding: 15px; background-color: #1e293b; border-radius: 8px; width: 30%; border: 1px solid #333; }}
    .flow-arrow {{ font-size: 2rem; color: #10b981; }}
    .breach-tag {{ background-color: #450a0a; color: #fca5a5; padding: 3px 8px; border-radius: 5px; font-size: 0.8rem; border: 1px solid #ef4444; margin-right: 5px; }}
    .status-item {{ padding: 10px; background-color: #0f172a; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid; }}
    .lockdown-banner {{ background-color: #ef4444; color: white; text-align: center; padding: 20px; font-size: 1.5rem; font-weight: bold; border-radius: 8px; animation: blinker 1.5s linear infinite; }}
    @keyframes blinker {{ 50% {{ opacity: 0.5; }} }}
    </style>
    """, unsafe_allow_html=True)

# --- 10 QUESTION QUIZ DATABASE ---
QUIZ_DATA = [
    {
        "question": "🚨 You receive an urgent email from 'campus-IT-support@gmail.com' stating your Wi-Fi access will be cut off unless you click a link to verify your identity. What should you do?",
        "options": ["Click the link and quickly verify.", "Forward it to your friends to warn them.", "Ignore it and report it as phishing.", "Reply to the sender asking for proof."],
        "answer": "Ignore it and report it as phishing.",
        "exp": "Official IT departments never use @gmail.com addresses and rarely create false urgency to force you into clicking links."
    },
    {
        "question": "☕ You are studying at a local cafe and need to check your bank balance. The cafe offers a free, open Wi-Fi network. Is it safe?",
        "options": ["Yes, if the cafe looks reputable.", "No, open Wi-Fi networks can be intercepted easily.", "Yes, as long as you use incognito mode.", "Yes, but only if you use a Mac."],
        "answer": "No, open Wi-Fi networks can be intercepted easily.",
        "exp": "Open networks lack encryption, making it easy for hackers to execute 'Man-in-the-Middle' attacks to steal your data."
    }
]

# --- SMART SIMULATED LLM ENGINE ---
def generate_smart_response(prompt):
    clean_text = " " + re.sub(r'[^\w\s]', '', prompt.lower()) + " "
    if any(w in clean_text for w in [" hi ", " hello ", " hey ", " help "]) or "who are you" in clean_text:
        return "Hello! I am the CampusShield AI Mentor. I can help you analyze threats, understand cybersecurity concepts, or guide you on campus IT policies. What's on your mind?"
    elif any(w in clean_text for w in ["phish", "pish", "link", "email", "fake", "spam", "click"]):
        return "It sounds like you might be dealing with a **Phishing attempt**! Scammers often use 'Typosquatting' (e.g., `netflíx.com` instead of `netflix.com`). Never click on urgent links. If you're unsure, let our Zero-Click Extension handle it, or paste suspicious commands in our DevSec Scanner."
    elif any(w in clean_text for w in ["password", "2fa", "otp", "login", "auth", "credential"]):
        return "Password security is crucial! Always use a unique passphrase for your university account and **enable 2FA**. You can check how fast a hacker could crack your current password in our 'Dashboard & Hygiene' section."
    elif any(w in clean_text for w in ["wifi", "wi-fi", "network", "public", "dorm", "hostel", "router"]):
        return "Hostel and Campus Wi-Fi networks can be vulnerable to packet sniffing (like Man-in-the-Middle attacks). **Always use the official encrypted network (like eduroam).** Avoid typing passwords on open 'Guest' networks unless using a trusted VPN."
    else:
        return "That's an interesting query! In the realm of cybersecurity, always adopt a **'Zero Trust'** mindset. Verify everything, whether it's a piece of code, a downloadable file, or an email from a professor. Can I help you scan a specific file or link today?"

# --- AUTHENTICATION & ADVANCED UEBA LOGIC ---
def auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>🛡️ CampusShield AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #888;'>Explainable Protection for Students & Campuses</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🧪 Hackathon Demo Controls")
        st.caption("Select a context to demonstrate the UEBA Engine to the judges:")
        scenario = st.selectbox("Simulate Login Context:", [
            "Normal: Campus Wi-Fi (Pune, India) via macOS",
            "Anomaly 1: Impossible Travel (Moscow, RU) via macOS",
            "Anomaly 2: Unknown Device (Pune, India) via Windows PC"
        ])
        st.markdown("---")
        
        email = st.text_input("Institutional Email", placeholder="student@campus.edu")
        
        if st.button("Secure Login (SSO)"):
            if email:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split('@')[0].capitalize()
                st.session_state.login_time = datetime.now().strftime("%H:%M:%S")
                
                if "Normal" in scenario:
                    st.session_state.is_anomaly = False
                    st.session_state.anomaly_reason = ""
                    st.session_state.current_device = "macOS"
                elif "Impossible Travel" in scenario:
                    st.session_state.is_anomaly = True
                    st.session_state.anomaly_reason = "Impossible Travel detected. Last login was Pune, India 2 hours ago. Current login from Moscow, RU is physically impossible."
                    st.session_state.current_device = "macOS"
                    broadcast_to_admin("UEBA_ALERT", "Impossible Travel Detected (Moscow)")
                elif "Unknown Device" in scenario:
                    st.session_state.is_anomaly = True
                    st.session_state.anomaly_reason = "Unrecognized Device Fingerprint. You normally use macOS, but this login is from an untrusted Windows PC."
                    st.session_state.current_device = "Windows PC"
                    broadcast_to_admin("UEBA_ALERT", "Unknown Device Login Attempt")
                    
                st.rerun()
            else:
                st.error("Please enter your campus email.")

# --- MAIN DASHBOARD ---
def main_dashboard():
    with st.sidebar:
        st.title(f"Hi, {st.session_state.user_name}!")
        st.caption(st.session_state.user_email)
        
        st.markdown(f"**Current Level:** Cyber Defender")
        st.markdown(f"**XP:** {st.session_state.xp_points} / 1000")
        st.progress(st.session_state.xp_points / 1000)
        
        st.markdown("**Your Trophies:**")
        for badge in st.session_state.badges:
            st.markdown(f'<span class="badge">{badge}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Engine Settings")
        npu_enabled = st.toggle("⚡ Enable Ryzen AI NPU", value=True, help="Offloads ML/Vision tasks to the neural processing unit for lower latency.")
        processing_time = 0.3 if npu_enabled else 2.5

        st.markdown("---")
        
        if st.session_state.lockdown_mode:
            st.markdown("<h3 style='color: white; text-align:center;'>SYSTEM LOCKED</h3>", unsafe_allow_html=True)
            if st.button("Disable Lockdown (Admin Only)"):
                st.session_state.lockdown_mode = False
                
                # Turn off admin lockdown in JSON if user resets it manually
                try:
                    with open(SHARED_FILE, 'r') as f: data = json.load(f)
                    data["lockdown"] = False
                    with open(SHARED_FILE, 'w') as f: json.dump(data, f)
                except: pass
                
                st.rerun()
            menu = "🔒 System Isolated"
        else:
            menu = st.radio("Main Navigation", [
                "📊 Dashboard & Hygiene", 
                "🌐 Zero-Click Integrations",
                "🔍 DevSec & Threat Scanner", 
                "🛡️ Privacy & Identity Lab", 
                "🎮 Cyber Arena (Micro-Learning)", 
                "🤖 AI Cyber Mentor"
            ])
            
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- LOCKDOWN SCREEN OVERRIDE ---
    if st.session_state.lockdown_mode:
        st.markdown("<div class='lockdown-banner'>🚨 DEFCON 1: EMERGENCY LOCKDOWN ACTIVE 🚨</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background-color: #450a0a; border: 2px solid #ef4444; padding: 30px; border-radius: 10px;">
            <h2 style="color: #fca5a5; text-align: center;">Account Isolated to Prevent Lateral Movement</h2>
            <ul style="color: #fca5a5; font-size: 1.1rem; line-height: 1.8;">
                <li>❌ All active sessions across other devices have been terminated.</li>
                <li>❌ Campus Wi-Fi authentication token revoked.</li>
                <li>❌ GitHub / GitLab API keys automatically rotated.</li>
                <li>❌ Access to University Intranet blocked.</li>
            </ul>
            <p style="color: white; text-align: center; margin-top: 20px;"><em>Please contact the IT Helpdesk at Ext. 4040 with your Student ID to verify your identity and restore access.</em></p>
        </div>
        """, unsafe_allow_html=True)
        return

    # SECTION 1: DASHBOARD & HYGIENE 
    if menu == "📊 Dashboard & Hygiene":
        
        col_title, col_panic = st.columns([3, 1])
        with col_title:
            st.title("Digital Hygiene & Security Overview")
        with col_panic:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚨 ACTIVATE LOCKDOWN"):
                with st.spinner("Initiating DEFCON 1... Killing sessions..."):
                    time.sleep(1.5)
                    st.session_state.lockdown_mode = True
                    broadcast_to_admin("PANIC_BUTTON", "User manually initiated account lockdown")
                    st.rerun()

        st.markdown("""
        <div class="live-ticker">
            <marquee behavior="scroll" direction="left" scrollamount="6" style="color: #60a5fa; font-family: monospace; font-size: 1.1rem; padding-top: 5px;">
                🔴 [LIVE] Blocked zero-day payload in Hostel Dorm 4... &nbsp;&nbsp;&nbsp;&nbsp; 🟢 [SYSTEM] Ryzen NPU operating at optimal latency (0.28s)... &nbsp;&nbsp;&nbsp;&nbsp; 🔴 [ALERT] Prevented credential harvest via fake Library portal... &nbsp;&nbsp;&nbsp;&nbsp; 🟢 [SAFE] Quarantined 14 phishing emails today.
            </marquee>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.is_anomaly:
            st.markdown(f"""
            <div class="ueba-alert">
                <strong>🚨 Context-Aware UEBA Alert:</strong> {st.session_state.anomaly_reason}
                <br><br><em>Action Taken: Step-up authentication (2FA) enforced to verify your identity.</em>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ueba-card">
                <strong>🤖 UEBA Engine Status:</strong> Location (Pune) and Device ({st.session_state.current_device}) match your historical baseline. 
                <span style="color:{t['primary']};">No anomalies detected.</span>
            </div>
            """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cyber Safety Score", "82/100", "5% Improve" if not st.session_state.is_anomaly else "-15% Drop")
        m2.metric("Threats Blocked", "4", "This Week")
        m3.metric("Account Status", "Protected" if st.session_state.two_fa else "Vulnerable", "-10 pts" if not st.session_state.two_fa else "")
        m4.metric("Active Session", "1", f"Device: {st.session_state.current_device}")

        st.markdown("---")
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.subheader("📈 Personal Cyber Risk Timeline")
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
            scores = [65, 68, 70, 75, 72, 80, 82]
            df_trend = pd.DataFrame({'Date': dates, 'Safety Score': scores})
            fig_trend = px.line(df_trend, x='Date', y='Safety Score', markers=True, color_discrete_sequence=[t['primary']])
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=320)
            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            st.subheader("Starter Checklist")
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.write("**1. Multi-Factor Authentication**")
            if not st.session_state.two_fa:
                if st.button("Enable Campus 2FA Now"):
                    st.session_state.two_fa = True
                    broadcast_to_admin("HYGIENE_UPDATE", "Enabled 2FA")
                    st.rerun()
            else:
                st.success("✅ 2FA is currently Active.")
            
            st.write("**2. Deep Dark Web Intelligence (OSINT)**")
            if not st.session_state.dark_web_scanned:
                if st.button("🔍 Run OSINT Breach Scan"):
                    with st.spinner("Querying underground forums, pastebins, and breach databases..."):
                        time.sleep(2)
                        st.session_state.dark_web_scanned = True
                        broadcast_to_admin("OSINT_CHECK", "Checked Dark Web (2 Exposures Found)")
                        st.rerun()
            else:
                st.error("🚨 2 Exposures Found on Dark Web")
                st.markdown("""
                <div style="background-color: #111; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #ef4444;">
                    <strong>Canva Data Incident (2019)</strong><br>
                    <span class="breach-tag">Email</span><span class="breach-tag">Passwords</span><span class="breach-tag">Names</span>
                </div>
                <div style="background-color: #111; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #ef4444;">
                    <strong>LinkedIn Breach (2012)</strong><br>
                    <span class="breach-tag">Email</span><span class="breach-tag">Passwords</span>
                </div>
                """, unsafe_allow_html=True)
                st.info("💡 **Action Required:** Ensure your campus password is not the same as your LinkedIn/Canva password.")
                if st.button("Reset Scan", type="secondary"):
                    st.session_state.dark_web_scanned = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 🔐 Advanced Credential Health Check (Local ML Processing)")
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        test_pw = st.text_input("Test your campus password pattern (Data never leaves your browser):", type="password")
        if test_pw:
            results = zxcvbn(test_pw)
            score = results['score']
            crack_time = results['crack_times_display']['offline_fast_hashing_1e10_per_second']
            st.progress(score / 4)
            if score <= 1: st.error(f"**🚨 Weak!** Estimated crack time: **{crack_time}**.")
            elif score == 2: st.warning(f"**⚠️ Moderate.** Estimated crack time: **{crack_time}**.")
            elif score == 3: st.info(f"**✅ Strong.** Estimated crack time: **{crack_time}**.")
            else: st.success(f"**🛡️ Very Strong!** Estimated crack time: **{crack_time}**.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 💻 Endpoint Posture (Zero-Trust Device Health)")
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.write("CampusShield verifies your device integrity before granting access to university networks to prevent lateral malware movement.")
        
        col_ep1, col_ep2 = st.columns([1, 1.5])
        
        with col_ep1:
            ep_score = 100 if st.session_state.endpoint_fixed else (65 if st.session_state.endpoint_scanned else 0)
            
            fig_ep = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ep_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Device Trust Score", 'font': {'color': t['text']}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#1e293b"},
                    'steps': [
                        {'range': [0, 50], 'color': "#ef4444"},
                        {'range': [50, 80], 'color': "#f59e0b"},
                        {'range': [80, 100], 'color': "#10b981"}
                    ],
                    'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': ep_score}
                }
            ))
            fig_ep.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=250, margin=dict(l=20, r=20, t=30, b=10))
            st.plotly_chart(fig_ep, use_container_width=True)

        with col_ep2:
            if not st.session_state.endpoint_scanned:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🖥️ Run Deep System Scan"):
                    with st.spinner("Checking OS Registry, Firewall Rules, and Browser Extensions..."):
                        time.sleep(2)
                        st.session_state.endpoint_scanned = True
                        broadcast_to_admin("HEALTH_SCAN", "Device Posture Scanned (Score: 65)")
                        st.rerun()
            else:
                st.markdown("#### 🔍 Telemetry Scan Results:")
                if not st.session_state.endpoint_fixed:
                    st.markdown("<div class='status-item' style='border-color: #10b981;'><span style='color:#10b981;'>✅ Firewall:</span> Active (Inbound/Outbound Rules Enforced)</div>", unsafe_allow_html=True)
                    st.markdown("<div class='status-item' style='border-color: #f59e0b;'><span style='color:#f59e0b;'>⚠️ OS Patch Level:</span> Missing Security Update KB5034441</div>", unsafe_allow_html=True)
                    st.markdown("<div class='status-item' style='border-color: #ef4444;'><span style='color:#ef4444;'>🚨 Browser:</span> Malicious extension 'PDF Merger Pro' detected reading DOM data.</div>", unsafe_allow_html=True)
                    
                    if st.button("🛠️ Auto-Fix Issues (Quarantine Ext & Update OS)"):
                        with st.spinner("Applying patches and sandboxing risky extensions..."):
                            time.sleep(1.5)
                            st.session_state.endpoint_fixed = True
                            broadcast_to_admin("AUTO_HEAL", "OS Updated and Malicious Extension Quarantined")
                            st.rerun()
                else:
                    st.markdown("<div class='status-item' style='border-color: #10b981;'><span style='color:#10b981;'>✅ Firewall:</span> Active</div>", unsafe_allow_html=True)
                    st.markdown("<div class='status-item' style='border-color: #10b981;'><span style='color:#10b981;'>✅ OS Patch Level:</span> Up to date (KB5034441 Installed)</div>", unsafe_allow_html=True)
                    st.markdown("<div class='status-item' style='border-color: #10b981;'><span style='color:#10b981;'>✅ Browser:</span> Clean. No risky extensions found.</div>", unsafe_allow_html=True)
                    st.success("Your device now meets the Zero-Trust compliance standards for campus network access.")
                    if st.button("Reset Scan", type="secondary"):
                        st.session_state.endpoint_scanned = False
                        st.session_state.endpoint_fixed = False
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 2: ZERO-CLICK INTEGRATIONS 
    elif menu == "🌐 Zero-Click Integrations":
        st.title("Frictionless Security (Zero-Click Defense)")
        st.write("We understand that students won't manually copy-paste every link. Here is how CampusShield protects users automatically without any extra clicks.")
        
        tab_ext, tab_email, tab_ide = st.tabs(["🧩 Browser Sandbox", "✉️ Invisible Payload Stripper", "👨‍💻 IDE Auto-Patch Bot"])
        
        with tab_ext:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("Zero-Click Web Protection")
            st.write("The CampusShield extension intercepts requests before the page loads. Now featuring Active Sandbox Detonation.")
            sim_link = st.text_input("Simulate clicking a link (e.g., from a WhatsApp message):", value="http://login-campus-verify.update-now.xyz")
            col_ext1, col_ext2 = st.columns([1, 4])
            with col_ext1:
                if st.button("Simulate Click 🖱️"):
                    st.session_state.ext_clicked = True
                    st.session_state.ext_url = sim_link
                    st.session_state.ext_detonated = False
                    broadcast_to_admin("LINK_CLICK", f"Phishing attempt blocked: {sim_link}")
            with col_ext2:
                if st.session_state.ext_clicked:
                    if st.button("Reset Simulation", type="secondary"):
                        st.session_state.ext_clicked = False
                        st.session_state.ext_detonated = False
                        st.rerun()
            if st.session_state.ext_clicked:
                st.markdown(f"""
                <div style="background-color: #ef4444; color: white; padding: 30px; border-radius: 10px; text-align: center; margin-top: 20px; border: 2px solid #b91c1c;">
                    <h1 style="color: white; margin-bottom: 0;">🛑 Access Blocked by CampusShield</h1>
                    <p style="font-size: 1.2rem;">The website you are trying to visit has been identified as a <strong>Phishing Threat</strong>.</p>
                    <p><strong>URL:</strong> {st.session_state.ext_url}</p>
                    <br>
                    <p><i>Reason: Typosquatting and low domain reputation detected by local AI engine.</i></p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if not st.session_state.ext_detonated:
                    if st.button("🔬 Detonate in AI Sandbox (Analyze Payload)"):
                        with st.spinner("Initializing Virtual Container... Opening link in isolated environment..."):
                            time.sleep(2.5)
                            st.session_state.ext_detonated = True
                            broadcast_to_admin("SANDBOX_DETONATE", "Payload detonated safely in sandbox VM")
                            st.rerun()
                else:
                    st.success("✅ **Detonation Complete.** Real device remained 100% insulated.")
                    st.markdown("### 🧬 Sandbox Telemetry Report")
                    st.markdown("""
                    <div class="forensics-term">
                    <span style="color: #60a5fa;">[SYSTEM]</span> Isolated VM initialized. Routing traffic through VPN.<br>
                    <span style="color: #60a5fa;">[NETWORK]</span> GET Request sent to: http://login-campus-verify.update-now.xyz<br>
                    <span style="color: #f59e0b;">[WARNING]</span> 3 Redirects detected.<br>
                    <span style="color: #ef4444;">[ALERT]</span> DOM loaded. Hidden <code>iframe</code> detected loading external script from <code>http://malware-c2-server.ru/hook.js</code><br>
                    <span style="color: #ef4444;">[ALERT]</span> Script attempting to access <code>document.cookie</code> (Session Hijacking attempt).<br>
                    <span style="color: #ef4444;">[ALERT]</span> Invisible background download triggered: <code>update_patch_x64.exe</code> (SHA256: 8a9...b21)<br>
                    <span style="color: #10b981;">[DEFENSE]</span> Payloads captured. Processes killed. Environment destroyed.<br>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_email:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("✉️ Invisible Payload Stripper (Pegasus-Style Zero-Click Defense)")
            st.write("Advanced hackers use 'Zero-Click' attacks, hiding malicious code inside image metadata (like SVG or JPEG files sent via messaging apps or emails). Your phone gets hacked the moment it tries to preview the image. CampusShield sanitizes files *before* they reach the inbox.")
            st.markdown("#### The Invisible Sanitization Flow")
            st.markdown(f"""
            <div class="stripper-flow">
                <div class="flow-box">
                    <h4>1. Incoming Attack</h4>
                    <p style="font-size: 0.8rem; color: #fca5a5;">Hacker sends <code>event_poster.jpg</code></p>
                    <p style="font-size: 0.7rem; color: #ef4444; font-family: monospace;">Hidden Payload:<br>&lt;script&gt;steal_token()&lt;/script&gt;</p>
                </div>
                <div class="flow-arrow">➡️</div>
                <div class="flow-box" style="border: 2px solid {t['primary']};">
                    <h4 style="color: {t['primary']};">2. CampusShield AI Filter</h4>
                    <p style="font-size: 0.8rem; color: #94a3b8;">Intercepts at Mail Server level.</p>
                    <p style="font-size: 0.7rem; color: #fbbf24;">Status: Stripping EXIF Headers...</p>
                </div>
                <div class="flow-arrow">➡️</div>
                <div class="flow-box">
                    <h4>3. Student Inbox</h4>
                    <p style="font-size: 0.8rem; color: #86efac;">Receives clean <code>event_poster.jpg</code></p>
                    <p style="font-size: 0.7rem; color: #10b981; font-family: monospace;">Payload: NULL (Removed)</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if not st.session_state.payload_stripped:
                if st.button("Simulate Incoming Zero-Click Attack"):
                    with st.spinner("Incoming message detected. Routing through CampusShield Sanitization Gateway..."):
                        time.sleep(2)
                        st.session_state.payload_stripped = True
                        broadcast_to_admin("ZERO_CLICK_PREVENT", "Stripped malicious EXIF payload from incoming image")
                        st.rerun()
            else:
                st.success("✅ **Threat Neutralized Silently.** The student received the image, but the malicious code was stripped. The student didn't have to click anything, and didn't even know they were attacked.")
                if st.button("Reset Attack Simulation", type="secondary"):
                    st.session_state.payload_stripped = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_ide:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("👨‍💻 Real-Time IDE Auto-Patch (VS Code Plugin)")
            st.write("CampusShield lives directly in the student's code editor. When they type a vulnerable or typosquatted package, the AI doesn't just warn them—it patches the code with a single click.")
            bad_code = "import os\nimport sys\nimport requests_v2  # Student misspelled 'requests'\n\ndef fetch_data():\n    pass"
            good_code = "import os\nimport sys\nimport requests  # AI Patched to official library\n\ndef fetch_data():\n    pass"
            st.text_area("Live IDE Editor:", value=good_code if st.session_state.ide_patched else bad_code, height=120, disabled=True)
            col_ide1, col_ide2 = st.columns([1, 1])
            with col_ide1:
                if not st.session_state.ide_scanned:
                    if st.button("Simulate Live Typing ⌨️"):
                        with st.spinner("IDE Background Scan..."):
                            time.sleep(1)
                            st.session_state.ide_scanned = True
                            st.rerun()
            if st.session_state.ide_scanned and not st.session_state.ide_patched:
                st.markdown("""
                <div style="background-color: #450a0a; border-left: 4px solid #ef4444; padding: 15px; margin-top: 10px; border-radius: 4px;">
                    <strong style="color: #ef4444;">🚨 Vulnerability Detected on Line 3</strong><br>
                    <span style="color: #fca5a5;">Package <code>requests_v2</code> is a known malicious typosquatting module. It steals environment variables.</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🛠️ AI Auto-Patch (Fix Code)"):
                    with st.spinner("Replacing malicious module with safe verified package..."):
                        time.sleep(1)
                        st.session_state.ide_patched = True
                        broadcast_to_admin("IDE_PATCH", "Auto-patched typosquatted package 'requests_v2'")
                        st.rerun()
            if st.session_state.ide_patched:
                st.success("✅ **Code Patched Successfully!** Malicious package removed and replaced with the safe, official `requests` module.")
                if st.button("Reset IDE", type="secondary"):
                    st.session_state.ide_scanned = False
                    st.session_state.ide_patched = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 3: DEVSEC & THREAT SCANNER 
    elif menu == "🔍 DevSec & Threat Scanner":
        st.title("DevSec & Threat Scanner")
        st.write("Upload suspicious files, verify terminal commands, or scan your source code before executing/committing.")
        
        scan_type = st.radio("Select Input Type:", [
            "Document / File Scan", 
            "🎥 Deepfake & Media Forensics",
            "💻 Terminal Command / Script Guard", 
            "📦 Software Installer Validator",
            "🔑 Source Code / API Secrets Scanner"
        ])
        
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        
        input_data = None
        input_type_flag = ""
        img_hash_val = None
        has_exif_data = False
        media_type = "" 
        actual_file_hash = ""
        expected_hash_input = ""
        
        if scan_type == "Document / File Scan":
            uploaded_file = st.file_uploader("Upload Assignment or PDF for Malware Scan", type=["pdf", "docx", "xlsx"])
            if uploaded_file: 
                input_data = uploaded_file.name
                input_type_flag = "file"
                st.session_state.file_sanitized = False 
                
        elif scan_type == "🎥 Deepfake & Media Forensics":
            st.info("💡 **Media Forensics:** Upload images, audio notes (voice clones), or video clips. Powered by AMD Ryzen NPU for edge-processing.")
            uploaded_media = st.file_uploader("Upload media file to detect AI manipulation", type=["jpg", "png", "jpeg", "mp4", "wav", "mp3"])
            if uploaded_media:
                file_ext = uploaded_media.name.split('.')[-1].lower()
                media_bytes = uploaded_media.getvalue()
                img_hash_val = hashlib.md5(media_bytes).hexdigest()
                if file_ext in ['jpg', 'png', 'jpeg']:
                    img = Image.open(uploaded_media)
                    st.image(img, width=250, caption="Uploaded Image")
                    has_exif_data = bool(img.getexif())
                    media_type = "image"
                elif file_ext in ['mp4']:
                    st.video(media_bytes)
                    media_type = "video"
                elif file_ext in ['wav', 'mp3']:
                    st.audio(media_bytes)
                    media_type = "audio"
                input_data = uploaded_media.name
                input_type_flag = "deepfake"
                
        elif scan_type == "💻 Terminal Command / Script Guard":
            st.info("💡 **Pro Tip:** Don't blindly run commands from StackOverflow or Github! Paste them here first.")
            input_data = st.text_area("Paste Command here (e.g., pip install tenserflow):", height=100)
            input_type_flag = "command"
            
        elif scan_type == "📦 Software Installer Validator":
            st.info("💡 **Supply Chain Defense:** Upload installers (like Git, VS Code) to verify they haven't been modified or infected by third-party download sites.")
            col_hash1, col_hash2 = st.columns(2)
            with col_hash1:
                uploaded_installer = st.file_uploader("Upload Installer (.exe, .zip, .msi)", type=["exe", "zip", "msi", "dmg"])
            with col_hash2:
                expected_hash_input = st.text_input("Expected SHA-256 Hash (from official website):", help="Leave blank to let our AI check against known malicious signatures.")
            if uploaded_installer:
                input_data = uploaded_installer.name
                input_type_flag = "installer"
                file_bytes = uploaded_installer.getvalue()
                actual_file_hash = hashlib.sha256(file_bytes).hexdigest()
                
        elif scan_type == "🔑 Source Code / API Secrets Scanner":
            st.info("💡 **DevSecOps Defense:** Scan your code to prevent leaking real AWS keys, or generate a **Honeytoken** to trap hackers.")
            sample_code = 'import boto3\n\n# Connect to database\ndb_uri = "mongodb+srv://admin:SuperSecretPass@campus-cluster.mongodb.net"\n\n# AWS Config\nAWS_KEY = "AKIAIOSFODNN7EXAMPLE"\nSECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"\n\ndef init_cloud():\n    pass'
            input_data = st.text_area("Paste your Python/JS code here:", value=sample_code, height=200)
            input_type_flag = "code_secrets"
            if st.button("🍯 Generate Cyber Trap (Honeytoken)"):
                st.session_state.honeytoken = f"AKIAFAKE{np.random.randint(10000, 99999)}TOKEN"
                broadcast_to_admin("HONEYTOKEN_DEPLOY", "Deployed fake AWS key in public repository")
                st.rerun()
            if st.session_state.honeytoken:
                st.markdown("---")
                st.success(f"**Fake AWS Key:** `{st.session_state.honeytoken}`")
                st.info("💡 **Instructions:** Paste this fake key into your public GitHub repository. If a hacker scrapes your code and attempts to use this key, the SOC will instantly detect their IP.")
                if st.button("Simulate Hacker Attempt"):
                    st.markdown(f"""
                    <div style="background-color: #450a0a; color: #fca5a5; padding: 20px; border-radius: 8px; border: 1px solid #ef4444; margin-top: 10px;">
                        <h3 style="color: #ef4444; margin-top: 0;">🚨 INTRUSION ALERT: Honeytoken Triggered!</h3>
                        <p>Someone just attempted to use your fake credentials.</p>
                        <ul><li><strong>Attacker IP:</strong> 45.33.XX.XX (Moscow, RU)</li><li><strong>Action Taken:</strong> IP Blocked. Real infrastructure remains 100% safe.</li></ul>
                    </div>
                    """, unsafe_allow_html=True)
                    broadcast_to_admin("INTRUSION_ALERT", "Honeytoken Triggered by IP 45.33.XX.XX")
        
        if input_data and input_type_flag:
            if st.button(f"Analyze with Ryzen NPU {'Vision/Voice' if input_type_flag == 'deepfake' else 'ML'} Models"):
                with st.status(f"Initializing AI Security Protocols... {'(Ryzen NPU Active)' if npu_enabled else '(CPU Fallback)'}", expanded=True) as status:
                    if input_type_flag == "deepfake" and media_type == "video":
                        st.write("🔍 Extracting container metadata...")
                        time.sleep(processing_time * 0.3)
                        st.write("🧠 NPU Offload: Decoding H.264 video frames (24 FPS)...")
                        time.sleep(processing_time * 0.5)
                        st.write("👁️ Running Spatial-Temporal inconsistencies checks...")
                    elif input_type_flag == "deepfake" and media_type == "audio":
                        st.write("🔍 Analyzing audio frequencies...")
                        time.sleep(processing_time * 0.3)
                        st.write("🧠 NPU Offload: Generating Mel-Spectrogram...")
                        time.sleep(processing_time * 0.5)
                        st.write("🎙️ Checking for AI Voice Cloning artifacts (ElevenLabs/VALL-E models)...")
                    else:
                        st.write("🔍 Extracting metadata and static signatures...")
                        time.sleep(processing_time * 0.3)
                        st.write("🧠 Loading Local ML Threat Models...")
                        time.sleep(processing_time * 0.4)
                        st.write("⚙️ Running heuristic analysis and pattern matching...")
                    time.sleep(processing_time * 0.3)
                    status.update(label="✅ AI Analysis Complete", state="complete", expanded=False)
                    
                st.markdown("---")
                
                is_scam = False
                values = [5, 5, 5, 5, 5]
                categories = ['Metric 1', 'Metric 2', 'Metric 3', 'Metric 4', 'Metric 5']
                cmd = "" 
                
                if input_type_flag == "deepfake":
                    seed_val = int(img_hash_val[:8], 16)
                    np.random.seed(seed_val)
                    if media_type == "image":
                        categories = ['Error Level (ELA) Risk', 'GAN Artifacts', 'Metadata Tampering', 'Text Overlay Anomaly', 'Pixel Density Mismatch']
                        values = [np.random.randint(15, 95), np.random.randint(10, 92), np.random.randint(10, 35) if has_exif_data else np.random.randint(75, 99), np.random.randint(5, 85), np.random.randint(10, 75)]
                    elif media_type == "video":
                        categories = ['Facial Micro-Expressions', 'Lip-Sync Sync Risk', 'Blinking Inconsistency', 'Background Warping', 'Deepfake GAN Noise']
                        values = [np.random.randint(40, 95), np.random.randint(50, 99), np.random.randint(20, 85), np.random.randint(10, 60), np.random.randint(50, 95)]
                    elif media_type == "audio":
                        categories = ['Spectrogram Anomaly', 'Breathing Pattern Risk', 'Synthetic Pitch Variance', 'Robotic Cadence', 'Background Noise Masking']
                        values = [np.random.randint(50, 95), np.random.randint(60, 99), np.random.randint(30, 85), np.random.randint(40, 90), np.random.randint(20, 75)]
                    avg_risk = sum(values) / len(values)
                    is_scam = avg_risk > 50 or max(values) > 85
                    if is_scam: 
                        st.error(f"🚨 HIGH RISK: Digital manipulation or AI-synthesis markers detected in the uploaded {media_type}.")
                        broadcast_to_admin("DEEPFAKE_DETECTED", f"Detected GAN artifacts in {media_type}")
                    else: st.success(f"✅ Clean: The {media_type} appears structurally organic and unaltered.")
                    np.random.seed(None)
                    
                elif input_type_flag == "file":
                    categories = ['Macro Infection Risk', 'Malicious Signature', 'Suspicious Payload Size', 'Hidden Executable', 'Metadata Anomalies']
                    values = [90, 85, 20, 10, 40]
                    is_scam = True
                    st.error(f"🚨 HIGH RISK: The file contains suspicious executable signatures (Hidden Macros).")
                    broadcast_to_admin("MALWARE_DETECT", "Macro Infection Risk found in document")
                
                elif input_type_flag == "command":
                    cmd = input_data.lower()
                    typo_risk = 95 if any(x in cmd for x in ["tenserflow", "twillo", "request ", "discord.js-hack"]) else 10
                    rce_risk = 90 if ("curl " in cmd or "wget " in cmd) and "|" in cmd and "bash" in cmd else 10
                    obfuscation = 85 if "base64" in cmd or "eval(" in cmd else 10
                    categories = ['Typosquatting (Fake Package)', 'Blind Execution (RCE)', 'Obfuscation Risk', 'Suspicious Source (HTTP)', 'Privilege Escalation (sudo)']
                    values = [typo_risk, rce_risk, obfuscation, 80 if "http://" in cmd else 10, 70 if "sudo " in cmd else 5]
                    is_scam = max(values) > 65
                    if is_scam: 
                        st.error("🚨 HIGH RISK: This command contains highly suspicious patterns or known malicious packages.")
                        broadcast_to_admin("THREAT_LOGGED", "Blocked malicious terminal execution")
                    else: st.success("✅ Clean: Command appears safe to execute.")
                    
                elif input_type_flag == "installer":
                    st.write(f"**Calculated File SHA-256:** `{actual_file_hash}`")
                    categories = ['Hash Mismatch Risk', 'Supply Chain Compromise', 'Malware Injection', 'Unofficial Signature', 'Data Exfiltration Potential']
                    if expected_hash_input:
                        if actual_file_hash.lower() == expected_hash_input.lower().strip():
                            is_scam = False
                            values = [5, 5, 5, 5, 5]
                            st.success("✅ HASH MATCH: The file is authentic and has exactly matched the official vendor release.")
                        else:
                            is_scam = True
                            values = [99, 95, 90, 100, 85]
                            st.error("🚨 CRITICAL HASH MISMATCH: The file has been modified! This is likely a Trojan or infected installer.")
                            broadcast_to_admin("THREAT_LOGGED", "Installer Hash Mismatch (Potential Trojan)")
                    else:
                        is_scam = True
                        values = [85, 80, 75, 90, 60]
                        st.warning("⚠️ UNKNOWN SIGNATURE: No official hash provided. Our AI scanner detects this file does not match standard known clean binaries.")

                elif input_type_flag == "code_secrets":
                    found_secrets = []
                    safe_code = input_data
                    if re.search(r'AKIA[0-9A-Z]{16}', safe_code):
                        found_secrets.append("Exposed AWS Access Key (AKIA...)")
                        safe_code = re.sub(r'AKIA[0-9A-Z]{16}', 'AKIA[REDACTED_BY_CAMPUSSHIELD]', safe_code)
                    if re.search(r'mongodb(\+srv)?:\/\/[a-zA-Z0-9_-]+:[a-zA-Z0-9_.-]+@', safe_code):
                        found_secrets.append("Exposed Database URI with Password (mongodb://...)")
                        safe_code = re.sub(r'mongodb(\+srv)?:\/\/[a-zA-Z0-9_-]+:[a-zA-Z0-9_.-]+@', 'mongodb://[REDACTED_USER]:[REDACTED_PASS]@', safe_code)
                    categories = ['AWS Key Leak Risk', 'Database Credentials', 'Hardcoded Passwords', 'Cloud Account Takeover', 'Data Breach Potential']
                    if found_secrets:
                        is_scam = True
                        values = [99 if "AWS" in str(found_secrets) else 10, 99 if "Database" in str(found_secrets) else 10, 90, 95, 85]
                        st.error("🚨 Critical Security Risk! You are about to expose credentials.")
                        for sec in found_secrets:
                            st.write(f"❌ **Detected:** {sec}")
                        st.markdown("#### Safe Redacted Code:")
                        st.markdown(f"<div class='code-snippet'>{safe_code.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                        broadcast_to_admin("API_KEY_MASKED", "Prevented API Key leak in source code")
                    else:
                        is_scam = False
                        values = [5, 5, 5, 5, 5]
                        st.success("✅ Clean! No obvious API keys or database credentials found in the code.")

                if input_type_flag in ["file", "installer"] and is_scam:
                    with st.expander("🔬 Deep Forensics View (Hex Dump & Extracted Strings)", expanded=False):
                        st.markdown("#### 🧬 Static Analysis (Suspicious Strings Extracted)")
                        st.code("EXTRACTING ASCII/UNICODE STRINGS...\n[+] http://malicious-c2-server.ru/drop.exe\n[+] CreateRemoteThread\n[+] VirtualAllocEx\n[+] WScript.Shell\n[+] AutoExecMacro", language="bash")
                        st.markdown("#### 🔢 Binary Hex Dump (PE Header Analysis)")
                        st.markdown('''
                        <div class="forensics-term">
                        <span class="hex-col">00000000</span> 4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00  <span class="ascii-col">MZ..............</span><br>
                        <span class="hex-col">00000010</span> B8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00  <span class="ascii-col">........@.......</span><br>
                        <span class="hex-col">00000020</span> 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  <span class="ascii-col">................</span><br>
                        <span class="hex-col">00000030</span> 00 00 00 00 00 00 00 00 00 00 00 00 80 00 00 00  <span class="ascii-col">................</span><br>
                        <span class="hex-col">00000040</span> 0E 1F BA 0E 00 B4 09 CD 21 B8 01 4C CD 21 54 68  <span class="ascii-col">........!..L.!Th</span><br>
                        <span class="hex-col">00000050</span> 69 73 20 70 72 6F 67 72 61 6D 20 63 61 6E 6E 6F  <span class="ascii-col">is program canno</span><br>
                        <span class="hex-col">00000060</span> 74 20 62 65 20 72 75 6E 20 69 6E 20 44 4F 53 20  <span class="ascii-col">t be run in DOS </span><br>
                        <span class="hex-col">00000070</span> 6D 6F 64 65 2E 0D 0D 0A 24 00 00 00 00 00 00 00  <span class="ascii-col">mode....$.......</span><br><br>
                        <span class="threat-str">[!] ANOMALY DETECTED: Suspicious Payload attached to end of file header.</span>
                        </div>
                        ''', unsafe_allow_html=True)

                st.markdown("### 🧠 Explainable AI Threat Breakdown")
                col_chart, col_exp = st.columns([1.5, 1])
                with col_chart:
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]], theta=categories + [categories[0]], fill='toself',
                        line_color='#ef4444' if is_scam else '#10b981',
                        fillcolor='rgba(239, 68, 68, 0.4)' if is_scam else 'rgba(16, 185, 129, 0.4)'
                    ))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=300, margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                with col_exp:
                    st.markdown("#### ✨ Teach-Back Mode")
                    st.info("Here is why the AI made this decision:")
                    if input_type_flag == "deepfake":
                        if media_type == "image":
                            if values[2] > 70: st.markdown("- **Metadata Tampering:** The EXIF data has been stripped.")
                            if values[0] > 70: st.markdown("- **Error Level Analysis:** Inconsistent compression levels detected.")
                            if values[1] > 70: st.markdown("- **GAN/AI Signs:** Neural network artifacts detected.")
                            if not is_scam: st.markdown("- **Safe:** Pixel arrays match standard camera outputs.")
                        elif media_type == "video":
                            if values[1] > 70: st.markdown("- **Lip-Sync Anomaly:** The audio does not perfectly match the mouth movements.")
                            if values[2] > 70: st.markdown("- **Blinking Rate:** Unnatural blinking patterns detected typical of AI models.")
                            if not is_scam: st.markdown("- **Safe:** Frame-by-frame temporal consistency verified.")
                        elif media_type == "audio":
                            if values[0] > 70: st.markdown("- **Spectrogram Void:** High-frequency cutoffs detected, typical of synthetic voice generation.")
                            if values[1] > 70: st.markdown("- **Breathing:** Lack of natural human breathing pauses between sentences.")
                            if not is_scam: st.markdown("- **Safe:** Vocal cord resonance patterns appear organic.")
                    elif input_type_flag == "file":
                        if values[0] > 50: st.markdown("- **Macro Infection Risk:** Dangerous macro scripts found hidden in the document.")
                    elif input_type_flag == "command":
                        if values[0] > 70: st.markdown("- **Typosquatting Alert:** You are trying to install a package with a misspelled name.")
                        if values[1] > 70: st.markdown("- **Blind Execution:** Piping `curl` directly into `bash` is extremely dangerous.")
                        if not is_scam: st.markdown("- **Safe:** Standard syntax. No known malicious packages detected.")
                    elif input_type_flag == "installer":
                        if values[0] > 50: st.markdown("- **Hash Mismatch:** A hash is a digital fingerprint. When the fingerprint doesn't match the official website, it means someone tampered with the file.")
                        if not is_scam: st.markdown("- **Verified:** The cryptographic signature exactly matches the expected vendor output.")
                    elif input_type_flag == "code_secrets":
                        if values[0] > 50: st.markdown("- **AWS Key Exfiltration:** Hackers use bots to scrape GitHub. They will use your account to mine crypto.")
                        if values[1] > 50: st.markdown("- **Database Breach:** Hardcoded MongoDB passwords allow attackers to steal user data.")
                        if not is_scam: st.markdown("- **Safe:** No standard API key formats detected.")

                if is_scam and input_type_flag in ["command", "file"]:
                    st.markdown("---")
                    st.markdown("### 🛠️ AI Auto-Heal (Remediation Engine)")
                    if input_type_flag == "command":
                        st.markdown("<div class='auto-heal-box'>", unsafe_allow_html=True)
                        if "tenserflow" in cmd or "twillo" in cmd:
                            corrected_cmd = cmd.replace("tenserflow", "tensorflow").replace("twillo", "twilio")
                            st.warning("⚠️ Detected known typosquatting package.")
                            st.success("✅ **CampusShield recommends using this safe command instead:**")
                            st.code(corrected_cmd, language="bash")
                        elif "bash" in cmd and "|" in cmd:
                            st.warning("⚠️ Detected blind remote execution (Piping to Bash).")
                            st.success("✅ **CampusShield Safe Action:** Download the script first, inspect it, then execute.")
                            st.code("# 1. Download\nwget [URL] -O script.sh\n\n# 2. Inspect\ncat script.sh\n\n# 3. Execute safely\nbash script.sh", language="bash")
                        st.markdown("</div>", unsafe_allow_html=True)
                    elif input_type_flag == "file":
                        st.markdown("<div class='auto-heal-box'>", unsafe_allow_html=True)
                        st.warning("⚠️ This document contains active executable macros.")
                        if not st.session_state.file_sanitized:
                            if st.button("Sanitize Document (Content Disarm & Reconstruction)"):
                                with st.spinner("Running CDR Engine: Stripping macros and rebuilding structure..."):
                                    time.sleep(2)
                                    st.session_state.file_sanitized = True
                                    broadcast_to_admin("FILE_SANITIZED", "CDR Engine neutralized document macros")
                                    st.rerun()
                        else:
                            st.success("✅ **File Sanitized!** All malicious macros have been neutralized.")
                            st.download_button(label="📥 Download Clean PDF", data=b"CLEAN_FILE_DATA", file_name=f"Clean_Sanitized_Document.pdf", mime="application/pdf")
                        st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### ⚡ Edge Computing Performance (NPU vs CPU)")
                df_perf = pd.DataFrame({
                    "Processor Type": ["Standard Cloud CPU", "Local Ryzen AI NPU"],
                    "Inference Latency (Seconds)": [2.5, 0.3]
                })
                colors = ["#1e293b", "#10b981"] if npu_enabled else ["#ef4444", "#1e293b"]
                fig_perf = px.bar(df_perf, x="Inference Latency (Seconds)", y="Processor Type", orientation='h', 
                                  color="Processor Type", color_discrete_sequence=colors,
                                  title="Local AI Processing Speed (Lower is Better)")
                fig_perf.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=200, showlegend=False)
                st.plotly_chart(fig_perf, use_container_width=True)

        if not input_data and scan_type != "🔑 Source Code / API Secrets Scanner":
            st.markdown("<br><div style='text-align: center; color: #64748b;'><i>Select an option above and upload data to unleash the Ryzen AI Engine.</i></div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 4: PRIVACY & IDENTITY LAB 
    elif menu == "🛡️ Privacy & Identity Lab":
        st.title("Privacy & Identity Protection")
        st.write("Ensure your academic submissions and public profiles do not leak Personally Identifiable Information (PII).")
        tab_text, tab_image, tab_csv, tab_social = st.tabs(["📝 Text Redactor", "🖼️ Image Masker", "📊 Dataset Anonymizer", "🕵️ Digital Footprint"])
        
        with tab_text:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            raw_text = st.text_area("Paste report or project text here:", height=150)
            if st.button("Redact PII from Text"):
                if raw_text:
                    with st.spinner(f"Running NER... {'(NPU Accelerated)' if npu_enabled else ''}"):
                        time.sleep(processing_time)
                        found_phone = bool(re.search(r'\b\d{10}\b', raw_text))
                        found_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', raw_text))
                        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[EMAIL REDACTED]', raw_text)
                        redacted = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', redacted)
                        st.success("PII successfully masked!")
                        st.text_area("Safe Text Output:", value=redacted, height=150)
                        broadcast_to_admin("PII_REDACTED", "Text PII locally redacted")
                        if found_phone or found_email:
                            st.markdown("#### 🧠 AI Explainability: Why did we redact this?")
                            if found_phone: st.info("📱 **Phone Number:** Hackers scrape phone numbers from public documents to launch targeted SMS Phishing (Smishing) or SIM-swapping attacks.")
                            if found_email: st.info("📧 **Email Address:** Exposed emails are added to dark-web spam lists, significantly increasing your risk of receiving credential harvesting links.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_image:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("🖼️ Visual PII Masker (OCR Engine)")
            st.write("Upload a screenshot of an ID card, event ticket, or document. The AI will blur out sensitive numbers, barcodes, and faces before you share it on WhatsApp or Social Media.")
            uploaded_pii_img = st.file_uploader("Upload Image containing PII", type=["jpg", "png", "jpeg"])
            if uploaded_pii_img:
                img_pii = Image.open(uploaded_pii_img)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original Image (Vulnerable)**")
                    st.image(img_pii, use_container_width=True)
                with col2:
                    if st.button("Apply AI Auto-Redaction"):
                        with st.spinner("Running Vision Models (Face & Text Detection)..."):
                            time.sleep(1.5)
                            redacted_img = img_pii.filter(ImageFilter.GaussianBlur(radius=15))
                            st.markdown("**Redacted Image (Safe to Share)**")
                            st.image(redacted_img, use_container_width=True)
                            st.success("✅ Sensitive regions masked successfully.")
                            st.caption("🔍 Simulated Detection: [Face Detected: 1], [ID Number Detected: 1]")
                            broadcast_to_admin("PII_REDACTED", "Image PII (Face/ID) locally redacted")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_csv:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            up = st.file_uploader("Upload CSV Data for Anonymization", type="csv")
            if up:
                df = pd.read_csv(up)
                st.write("Original Data Snippet:")
                st.dataframe(df.head(2))
                if st.button("Apply Privacy-By-Design Masking"):
                    for col in df.columns:
                        if any(x in col.lower() for x in ['name', 'id', 'email', 'phone']):
                            df[col] = df[col].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:10])
                    st.success("Data Anonymized! Safe for Lab Submission.")
                    st.dataframe(df.head(3))
                    broadcast_to_admin("DATASET_ANONYMIZED", "CSV Dataset cryptographically hashed")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_social:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("🕵️ Digital Footprint & Oversharing Risk")
            st.write("Analyze your public social media bio for potential security and physical risks.")
            bio_text = st.text_area("Paste Social Media Bio:", "CS Freshman @ Campus University 🎓 | Dorm 4B | 📱 9876543210 | 📧 student@college.edu")
            if st.button("Run Profile Audit"):
                with st.spinner("Running Semantic Privacy Analysis..."):
                    time.sleep(processing_time)
                    risk_score = 5 
                    categories = {"Physical": [], "Identity": [], "Phishing": []}
                    if re.search(r'\b\d{10}\b', bio_text): 
                        risk_score += 45
                        categories["Identity"].append("Phone Number exposed (Can be used for SIM swapping or OSINT tracking).")
                    if "dorm" in bio_text.lower() or "room" in bio_text.lower() or "hostel" in bio_text.lower(): 
                        risk_score += 40
                        categories["Physical"].append("Exact physical location exposed (High Stalking Risk).")
                    if "@" in bio_text and "." in bio_text: 
                        risk_score += 15
                        categories["Phishing"].append("Email address exposed (Will be scraped for spam/phishing lists).")
                    risk_score = min(risk_score, 100) 
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = risk_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Privacy Risk Score", 'font': {'color': t['text']}},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "#1e293b"},
                            'steps': [{'range': [0, 30], 'color': "#10b981"}, {'range': [30, 70], 'color': "#f59e0b"}, {'range': [70, 100], 'color': "#ef4444"} ],
                            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': risk_score}
                        }
                    ))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=280, margin=dict(l=20, r=20, t=40, b=20))
                    col_chart, col_details = st.columns([1, 1.5])
                    with col_chart:
                        st.plotly_chart(fig, use_container_width=True)
                    with col_details:
                        st.markdown("### Threat Breakdown")
                        if risk_score <= 30:
                            st.success("✅ **Profile Safe:** Excellent Operational Security (OPSEC). No obvious sensitive data found.")
                        else:
                            st.error("🚨 **High Risk Detected:** You are oversharing sensitive info on a public platform.")
                            for cat, alerts in categories.items():
                                if alerts:
                                    st.markdown(f"**⚠️ {cat} Risk:**")
                                    for a in alerts:
                                        st.markdown(f"- {a}")
            st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 5: MICRO-LEARNING HUB
    elif menu == "🎮 Cyber Arena (Micro-Learning)":
        st.title("🎮 Cyber Arena: Learn & Earn")
        st.write("Defend the campus, earn XP, and climb the Global Leaderboard by completing daily cyber challenges.")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Current Level", "Cyber Defender")
        col_s2.metric("Total XP", f"{st.session_state.xp_points} XP", "+50 XP Today")
        col_s3.metric("Daily Streak", f"🔥 {st.session_state.daily_streak} Days")
        col_s4.metric("Campus Rank", "#42", "Top 10%")
        st.markdown("---")
        tab_daily, tab_leaderboard, tab_bites = st.tabs(["🎯 10-Question Cyber Challenge", "🏆 Campus Leaderboard", "📖 Survival Guide"])
        
        with tab_daily:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            if not st.session_state.quiz_completed:
                q = QUIZ_DATA[st.session_state.quiz_index]
                st.subheader(f"Question {st.session_state.quiz_index + 1} of 10")
                st.progress((st.session_state.quiz_index) / 10)
                st.write(q['question'])
                selected_option = st.radio("Choose your answer:", q['options'], key=f"quiz_radio_{st.session_state.quiz_index}", disabled=st.session_state.show_explanation)
                if not st.session_state.show_explanation:
                    if st.button("Submit Answer"):
                        st.session_state.show_explanation = True
                        if selected_option == q['answer']:
                            st.session_state.quiz_score += 1
                        st.rerun()
                else:
                    if selected_option == q['answer']: st.success("🎉 Correct!")
                    else: st.error(f"❌ Incorrect. The right answer is: {q['answer']}")
                    st.info(f"💡 **Why?** {q['exp']}")
                    if st.button("Next Question ➡️" if st.session_state.quiz_index < 9 else "Finish Challenge 🏁"):
                        st.session_state.show_explanation = False
                        st.session_state.quiz_index += 1
                        if st.session_state.quiz_index >= len(QUIZ_DATA):
                            st.session_state.quiz_completed = True
                        st.rerun()
            else:
                st.balloons()
                st.success(f"### 🏆 Challenge Completed!")
                st.write(f"You scored **{st.session_state.quiz_score} out of 10**.")
                xp_earned = st.session_state.quiz_score * 25
                st.write(f"You earned **+{xp_earned} XP** for your efforts!")
                if st.button("Claim XP & Restart Training"):
                    st.session_state.xp_points += xp_earned
                    if st.session_state.quiz_score >= 8 and "🎓 Threat Hunter" not in st.session_state.badges:
                        st.session_state.badges.append("🎓 Threat Hunter")
                    broadcast_to_admin("ARENA_COMPLETED", f"Earned {xp_earned} XP in Cyber Arena")
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_completed = False
                    st.session_state.show_explanation = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_leaderboard:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("🏆 Top Campus Defenders")
            st.write("Students who have blocked the most threats and completed the most training modules.")
            leaderboard_data = {
                "Rank": ["🥇 1", "🥈 2", "🥉 3", "4", "42"],
                "Student (Anonymized)": ["Anon_83F2", "Anon_19A4", "Anon_77B1", "Anon_92C3", f"You ({st.session_state.user_name})"],
                "Department": ["Computer Science", "Business", "Mechanical", "Arts", "Your Dept"],
                "Total XP": ["4,200", "3,850", "3,100", "2,950", f"{st.session_state.xp_points}"],
                "Title": ["Cyber Ninja", "Cyber Ninja", "Threat Hunter", "Threat Hunter", "Cyber Defender"]
            }
            df_leaderboard = pd.DataFrame(leaderboard_data)
            st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_bites:
            st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
            st.subheader("💡 Today's 2-Min Tip: Malicious OAuth")
            st.info("When a site asks to 'Login with Google/Campus ID', always check the URL. Scammers use fake login popups to steal OAuth tokens. Always verify the domain name in the address bar!")
            if st.button("Mark as Read (+20 XP)"):
                st.session_state.xp_points += 20
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 6: AI CYBER MENTOR
    elif menu == "🤖 AI Cyber Mentor":
        st.title("🤖 Your Personal Cyber Mentor")
        st.write("Ask me anything about cybersecurity, campus policies, or get help with a current threat.")
        col_chat, col_info = st.columns([2, 1])
        
        with col_info:
            st.markdown("""
            <div class='feature-box' style='text-align: center; padding: 30px 20px;'>
                <div style='font-size: 4rem; margin-bottom: 10px;'>🧠</div>
                <h3 style='margin-bottom: 5px; color: #10b981;'>Ryzen-AI Core</h3>
                <span style='background-color: rgba(16, 185, 129, 0.2); color: #10b981; padding: 5px 15px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #10b981;'>🟢 System Online</span>
                <hr style='border-color: #333; margin: 20px 0;'>
                <div style='text-align: left; font-size: 0.9rem; color: #cbd5e1;'>
                    <strong>Loaded Knowledge Base:</strong><br><br>
                    <span style='color: #10b981;'>✓</span> Campus IT Security Policies<br>
                    <span style='color: #10b981;'>✓</span> Global Phishing Patterns<br>
                    <span style='color: #10b981;'>✓</span> Student Data Protection Act
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### ⚡ Quick Actions")
            if st.button("🛡️ Secure my dorm Wi-Fi"):
                st.session_state.messages.append({"role": "user", "content": "How can I secure my dorm Wi-Fi connection?"})
                st.session_state.messages.append({"role": "assistant", "content": "Hostel and Campus Wi-Fi networks can be vulnerable to packet sniffing. **Always use the official encrypted network (like eduroam).** Avoid typing passwords on open 'Guest' networks unless using a trusted VPN."})
                st.rerun()
                
        with col_chat:
            chat_container = st.container(height=250)
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
            if prompt := st.chat_input("Type your cyber question here (e.g., 'How to spot a deepfake?')..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing intent with Local NLP..."):
                        time.sleep(processing_time)
                        smart_response = generate_smart_response(prompt)
                        st.markdown(smart_response)
                        st.session_state.messages.append({"role": "assistant", "content": smart_response})

# --- ROUTING ---
if not st.session_state.logged_in: auth_page()
else: main_dashboard()