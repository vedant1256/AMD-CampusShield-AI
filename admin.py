import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import hashlib
import json
import os
from datetime import datetime, timedelta

# --- BRIDGE SETUP (Connects Admin to User) ---
SHARED_FILE = "swarm_data.json"

def read_shared_state():
    """Reads live telemetry data coming from user nodes."""
    if os.path.exists(SHARED_FILE):
        try:
            with open(SHARED_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"telemetry": [], "lockdown": False}

def set_admin_lockdown(status):
    """Sends a global DEFCON 1 signal to all user nodes."""
    data = read_shared_state()
    data["lockdown"] = status
    try:
        with open(SHARED_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

# --- CONFIGURATION & THEME (Emerald Guardian - Admin Edition) ---
st.set_page_config(
    page_title="CampusShield | Institution Admin", 
    page_icon="🛡️",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- THEME PALETTE (Synced with user.py) ---
t = {
    "bg": "#0f172a", "sidebar": "#1e293b", "primary": "#10b981", 
    "text": "#f8fafc", "accent": "#34d399", "card": "#1e293b"
}

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; transition: background-color 0.5s ease; }}
    [data-testid="stSidebar"] {{ background-color: {t['sidebar']} !important; border-right: 1px solid {t['primary']}33; }}
    .stButton>button {{ border-radius: 6px; background-color: {t['primary']}; color: white; border: none; font-weight: bold; width: 100%; }}
    .stMetric {{ background-color: {t['card']}; border: 1px solid #333; padding: 15px; border-radius: 10px; }}
    h1, h2, h3 {{ color: {t['primary']}; font-family: 'Segoe UI', sans-serif; }}
    .admin-card {{ border-left: 4px solid {t['primary']}; padding: 15px; background-color: {t['card']}; border-radius: 5px; margin-bottom: 20px; border: 1px solid #333; }}
    .alert-card {{ border-left: 4px solid #ef4444; padding: 15px; background-color: #450a0a55; border-radius: 5px; margin-bottom: 20px; }}
    .live-ticker-admin {{ background-color: #020617; border-left: 4px solid {t['primary']}; padding: 10px; margin-bottom: 20px; border-radius: 4px; color: #10b981; font-family: monospace; }}
    .forensics-term {{ background-color: #020617; color: #10b981; font-family: 'Courier New', Courier, monospace; padding: 15px; border-radius: 5px; height: 350px; overflow-y: scroll; border: 1px solid #333; font-size: 0.9rem; }}
    </style>
    """, unsafe_allow_html=True)

# Fetch Live Data
live_swarm_data = read_shared_state()

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
st.session_state.lockdown_active = live_swarm_data.get("lockdown", False)

# --- UI: LOGIN PAGE ---
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🛡️ CampusShield Admin")
        st.subheader("Institutional Command Center")
        
        username = st.text_input("Admin Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Access SOC Console"):
            if username.lower().strip() == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.user_role = "IT Admin"
                st.rerun()
            else:
                st.error("Access Denied: Invalid Username or Password")
    st.stop()

# --- ROUTING & SIDEBAR ---
st.sidebar.title("🛡️ Campus SOC")
st.sidebar.write(f"Role: **{st.session_state.user_role}**")
st.sidebar.markdown("---")

if st.session_state.lockdown_active:
    st.sidebar.error("🚨 EMERGENCY LOCKDOWN ACTIVE")
    if st.sidebar.button("DEACTIVATE LOCKDOWN"):
        set_admin_lockdown(False)
        st.rerun()

menu = st.sidebar.radio("Console Navigation", [
    "🌐 Threat Intelligence", 
    "📈 Swarm Analytics", 
    "🚨 Incident Response", 
    "⚖️ Compliance Audit",
    "📢 Awareness Broadcasting"
])

if st.sidebar.button("Secure Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- CONSOLE A: THREAT INTELLIGENCE ---
if menu == "🌐 Threat Intelligence":
    st.title("🌐 Campus Swarm Intelligence Hub")
    
    st.markdown("""
    <div class="live-ticker-admin">
        <marquee behavior="scroll" direction="left" scrollamount="5">
            🟢 [PREDICTIVE] High probability of phishing targeting Admin Block... 🟢 [SWARM] 1,450 Ryzen NPU nodes synced... 🔵 [INFO] Real-time telemetry connection established.
        </marquee>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    telemetry_count = len(live_swarm_data.get("telemetry", []))
    
    m1.metric("Collective NPU Power", "4.2 TFLOPS", "Swarm Active")
    m2.metric("Live Threat Signals", str(4120 + telemetry_count), f"+{telemetry_count} New")
    m3.metric("Edge Latency", "0.28s", "Ryzen NPU")
    m4.metric("Predicted Campus Risk", "8%", "Low", delta_color="inverse")

    st.markdown("---")
    tab_overview, tab_health, tab_feed = st.tabs(["🔮 Predictive Overview", "🧬 Swarm Node Health", "🛰️ Live Signature Feed"])
    
    with tab_overview:
        col_map, col_predict = st.columns([1.5, 1])
        with col_map:
            st.subheader("📍 Real-time Threat Heatmap")
            map_data = pd.DataFrame({
                'lat': [18.5204, 18.5210, 18.5220, 18.5190, 18.5230],
                'lon': [73.8567, 73.8570, 73.8580, 73.8560, 73.8590],
                'intensity': [10, 50, 30, 15, 45],
                'Zone': ['Hostel A', 'CS Lab', 'Mechanical', 'Admin', 'Library']
            })
            fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", size="intensity", color="intensity",
                                      color_continuous_scale='Reds', zoom=15, mapbox_style="carto-darkmatter", title="Active Attack Surface")
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']))
            st.plotly_chart(fig_map, use_container_width=True)

        with col_predict:
            st.subheader("🔮 24H Risk Forecast")
            forecast_times = [(datetime.now() + timedelta(hours=i)).strftime('%H:%M') for i in range(0, 24, 4)]
            risk_levels = [10, 15, 45, 30, 20, 15] 
            fig_forecast = px.area(x=forecast_times, y=risk_levels, title="Projected Threat Probability",
                                  labels={'x': 'Time', 'y': 'Risk %'}, markers=True, color_discrete_sequence=[t['primary']])
            fig_forecast.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=300)
            st.plotly_chart(fig_forecast, use_container_width=True)

    with tab_health:
        st.markdown("<div class='admin-card'>Monitor the collective compute power generated by student devices serving as Edge-AI sensors across the campus.</div>", unsafe_allow_html=True)
        col_h1, col_h2 = st.columns([1, 1.5])
        with col_h1:
            st.subheader("Active Swarm Nodes")
            fig_nodes = go.Figure(go.Indicator(
                mode = "gauge+number", value = 1450, domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Online NPUs", 'font': {'color': t['text']}},
                gauge = { 'axis': {'range': [None, 2000]}, 'bar': {'color': t['primary']}, 'bgcolor': "rgba(0,0,0,0)"}
            ))
            fig_nodes.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=300)
            st.plotly_chart(fig_nodes, use_container_width=True)

        with col_h2:
            st.subheader("Collective Processing Power Saved")
            tflops_data = pd.DataFrame({
                'Time': ['08:00', '10:00', '12:00', '14:00', '16:00'],
                'Cloud Compute Saved (TFLOPS)': [1.2, 2.5, 4.2, 3.8, 2.1]
            })
            fig_tflops = px.bar(tflops_data, x='Time', y='Cloud Compute Saved (TFLOPS)', text_auto=True, color_discrete_sequence=[t['accent']])
            fig_tflops.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=300)
            st.plotly_chart(fig_tflops, use_container_width=True)

    with tab_feed:
        st.subheader("🛰️ Live Swarm Signature Exchange")
        col_feed, col_btn = st.columns([4, 1])
        with col_btn:
            if st.button("🔄 Refresh Data"):
                st.rerun()
                
        telemetry_events = live_swarm_data.get("telemetry", [])
        if telemetry_events:
            feed_data = []
            for e in telemetry_events:
                feed_data.append({
                    "Time": e["timestamp"], 
                    "Source Node": e["node_id"], 
                    "Detected Event": e["action"], 
                    "Threat Details": e["threat"]
                })
            df_feed = pd.DataFrame(feed_data)
            st.dataframe(df_feed, use_container_width=True, hide_index=True)
        else:
            st.info("Waiting for live telemetry from student nodes... Run a scan in the User Portal to see data here.")

# --- CONSOLE B: SWARM ANALYTICS ---
elif menu == "📈 Swarm Analytics":
    st.title("📈 Swarm Behavioral Analytics")
    st.markdown("<div class='admin-card'><strong>Privacy Protocol:</strong> All student telemetry is anonymized using SHA-256 hashing.</div>", unsafe_allow_html=True)
    
    tab_ueba, tab_arena, tab_zt = st.tabs(["🧠 UEBA Matrix (Risk Clustering)", "🎮 Gamification ROI", "🛡️ Zero-Trust Campus Posture"])
    
    with tab_ueba:
        st.subheader("User & Entity Behavior Analytics (Departmental)")
        ueba_data = pd.DataFrame({
            'Department': ['Computer Science', 'Mechanical', 'Business', 'Arts', 'Library Staff', 'Hostel Block A'],
            'Average Risk Score': [20, 65, 45, 80, 15, 75],
            'Phishing Clicks (Last 7 Days)': [2, 18, 12, 25, 1, 30],
            'Node Count': [450, 320, 300, 200, 40, 150]
        })
        fig_ueba = px.scatter(ueba_data, x='Average Risk Score', y='Phishing Clicks (Last 7 Days)', 
                              size='Node Count', color='Average Risk Score', hover_name='Department',
                              color_continuous_scale='RdYlGn_r', title="Departmental Risk Clusters")
        fig_ueba.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=400)
        st.plotly_chart(fig_ueba, use_container_width=True)

    with tab_arena:
        st.subheader("Cyber Arena Impact (ROI)")
        col_chart, col_leader = st.columns([1.5, 1])
        with col_chart:
            arena_data = pd.DataFrame({
                'Week': ['W1', 'W2', 'W3', 'W4'],
                'Arena XP Earned': [12000, 25000, 48000, 85000],
                'Real Security Incidents': [85, 60, 42, 18]
            })
            fig_impact = go.Figure()
            fig_impact.add_trace(go.Bar(x=arena_data['Week'], y=arena_data['Arena XP Earned'], name='Arena XP', marker_color=t['primary'], opacity=0.6))
            fig_impact.add_trace(go.Scatter(x=arena_data['Week'], y=arena_data['Real Security Incidents'], name='Real Threats', line=dict(color='#ef4444', width=3), yaxis='y2'))
            fig_impact.update_layout(
                yaxis2=dict(title='Security Incidents', overlaying='y', side='right'),
                yaxis=dict(title='XP Earned'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_impact, use_container_width=True)
            
        with col_leader:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("#### 🏆 Department Arena Leaderboard")
            dept_leaderboard = pd.DataFrame({
                'Rank': ['🥇 1', '🥈 2', '🥉 3', '4'],
                'Department': ['Computer Science', 'Business', 'Mechanical', 'Arts'],
                'Total XP': ['2.1M', '1.8M', '900k', '450k']
            })
            st.dataframe(dept_leaderboard, hide_index=True, use_container_width=True)

    with tab_zt:
        st.subheader("Campus-Wide Zero-Trust Posture")
        zt_categories = ['Device Health', 'Identity (2FA)', 'Network Safety', 'App Security', 'Data Privacy']
        zt_scores = [85, 92, 78, 65, 100]
        fig_zt = go.Figure()
        fig_zt.add_trace(go.Scatterpolar(
            r=zt_scores + [zt_scores[0]], theta=zt_categories + [zt_categories[0]], 
            fill='toself', line_color=t['primary'], fillcolor='rgba(16, 185, 129, 0.4)'
        ))
        fig_zt.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=400)
        st.plotly_chart(fig_zt, use_container_width=True)

# --- CONSOLE C: INCIDENT RESPONSE ---
elif menu == "🚨 Incident Response":
    st.title("🚨 Live Security Operations Center (SOC)")

    st.markdown("<div class='admin-card'><strong>SOAR Engine Active:</strong> Security Orchestration, Automation, and Response.</div>", unsafe_allow_html=True)

    tab_terminal, tab_triage, tab_defcon = st.tabs(["📟 Live Edge Telemetry", "🛠️ Active Triage (SOAR)", "🛑 Global Kill-Switch"])

    with tab_terminal:
        col_term, col_ref = st.columns([4, 1])
        with col_term:
            st.subheader("📟 Raw Edge Telemetry Stream")
        with col_ref:
            if st.button("🔄 Sync Feed"): st.rerun()
            
        telemetry_events = live_swarm_data.get("telemetry", [])
        if not telemetry_events:
            log_entries = ["[SYSTEM] Listening for NPU events from campus network..."]
        else:
            log_entries = [f"[{e['timestamp']}] 🔵 NODE_{e['node_id']} TRIGGERED {e['action']}: {e['threat']}" for e in telemetry_events]
            
        st.markdown(f"<div class='forensics-term' style='height: 350px;'>{'<br>'.join(log_entries)}<br><span style='animation: blinker 1s linear infinite;'>_</span></div>", unsafe_allow_html=True)

    with tab_triage:
        st.subheader("Actionable Incident Queue")
        with st.expander("🔴 CRITICAL: Zero-Click Payload Detected in Library Wi-Fi", expanded=True):
            st.markdown("**Incident ID:** INC-991 | **Source:** Node HASH_88C1 | **Type:** Pegasus-style Image Exploit")
            st.info("🤖 **AI Recommended Playbook:** Sanitize image via CDR and push new hash signature to Swarm.")
            if st.button("Execute Playbook (Auto-Sanitize)"):
                st.success("✅ Playbook Executed: Threat neutralized.")

    with tab_defcon:
        st.subheader("🛡️ Strategic Kill-Switch: DEFCON 1")
        st.error("⚠️ WARNING: Activating DEFCON 1 will force all students into Read-Only Safe Mode.")
        
        if not st.session_state.lockdown_active:
            if st.button("🚨 INITIATE GLOBAL SYSTEM LOCKDOWN", use_container_width=True):
                with st.status("Executing Protocol 0: Isolating Intranet...", expanded=True) as status:
                    set_admin_lockdown(True)
                    st.session_state.lockdown_active = True
                    time.sleep(1)
                    status.update(label="SYSTEM ISOLATED: DEFCON 1 ACTIVE", state="complete")
                    st.rerun()
        else:
            st.markdown("""
                <div style="background-color: #450a0a; border: 3px solid #ef4444; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="color: #ef4444; margin: 0;">🛑 CAMPUS ISOLATED</h1>
                    <p style="color: white;">External traffic blocked. Read-only mode enabled for students.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔓 Restore Normal Operations"):
                set_admin_lockdown(False)
                st.session_state.lockdown_active = False
                st.rerun()

# --- CONSOLE D: COMPLIANCE AUDIT ---
elif menu == "⚖️ Compliance Audit":
    st.title("⚖️ Zero-Knowledge Compliance Vault")
    st.markdown("<div class='admin-card'><strong>DPDP Act & GDPR Ready:</strong> All telemetry is cryptographically hashed at the edge.</div>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("Anonymization Engine", "Active", "SHA-256")
    col_c2.metric("Local PII Retained", "142 GB", "Secured at Edge")
    col_c3.metric("Data Retention", "30 Days", "Auto-Purge")
    col_c4.metric("Audit Readiness", "99.8%", "PASS")

    st.markdown("---")
    tab_matrix, tab_pii, tab_ledger = st.tabs(["📜 DPDP/GDPR Matrix", "🛡️ Local PII Redaction", "🔗 Immutable Audit Ledger"])
    
    with tab_matrix:
        st.subheader("Legal Framework Adherence")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### Data Minimization")
            st.progress(100)
            st.markdown("#### Purpose Limitation")
            st.progress(100)
        with col_m2:
            st.markdown("#### Storage Limitation")
            st.progress(100)
            st.markdown("#### Right to Erasure")
            st.progress(100)

    with tab_pii:
        st.subheader("Edge AI: Data Prevented from Cloud Exposure")
        pii_data = pd.DataFrame({
            'PII Type': ['Phone Numbers', 'Email Addresses', 'Credentials', 'Location Data', 'Financial/IDs'],
            'Incidents Blocked at Edge': [420, 850, 310, 560, 120]
        })
        fig_pii = px.bar(pii_data, x='PII Type', y='Incidents Blocked at Edge', color='PII Type', color_discrete_sequence=px.colors.sequential.Teal)
        fig_pii.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']))
        st.plotly_chart(fig_pii, use_container_width=True)

    with tab_ledger:
        st.subheader("Live Cryptographic Audit Trail")
        if st.button("🔄 Refresh Ledger"): st.rerun()
        
        telemetry_events = live_swarm_data.get("telemetry", [])
        if telemetry_events:
            ledger_data = []
            for e in telemetry_events:
                ledger_data.append({
                    "Timestamp": e["timestamp"],
                    "Node_Hash (SHA-256)": e["node_id"] + hashlib.sha256(e["timestamp"].encode()).hexdigest()[:8],
                    "Action_Taken": e["action"],
                    "Ledger_Checksum": hashlib.md5(f"{e['node_id']}{e['action']}".encode()).hexdigest()
                })
            df_ledger = pd.DataFrame(ledger_data)
            st.dataframe(df_ledger, use_container_width=True, hide_index=True)
        else:
            st.info("No recent logs found. User actions will populate here.")

# --- CONSOLE E: AWARENESS BROADCASTING ---
elif menu == "📢 Awareness Broadcasting":
    st.title("📢 Awareness & Campaign Manager")
    st.markdown("<div class='admin-card'>Control the flow of security knowledge.</div>", unsafe_allow_html=True)
    
    tab_arena, tab_phishing, tab_alerts = st.tabs(["🎯 Arena Challenge Deployer", "🎣 Phishing Simulator", "🚨 Emergency Broadcast"])

    with tab_arena:
        st.subheader("Deploy New Cyber Arena Module")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            challenge_type = st.selectbox("Challenge Template", ["Browser Hygiene 101", "Phishing Simulation", "Secret Leak Detection"])
            xp_reward = st.slider("XP Reward Value", 50, 500, 250)
        with col_t2:
            target_group = st.multiselect("Target Audience", ["All Students", "First-Years", "CS/IT Dept"], default=["All Students"])
        if st.button("🚀 Push to Cyber Arena"):
            st.success(f"SUCCESS: Module is now live. Broadcast ID: ARENA_{hashlib.md5(challenge_type.encode()).hexdigest()[:6].upper()}")
            st.balloons()

    with tab_phishing:
        st.subheader("Run Campus-Wide Phishing Simulation")
        if st.button("📧 Launch Phishing Simulation"):
            st.success(f"Simulation Launched! Monitoring response rates...")
        
        sim_data = pd.DataFrame({
            'Action': ['Emails Delivered', 'Opened', 'Clicked Link (Failed)', 'Reported to IT (Passed)'],
            'Count': [4500, 3200, 450, 1200]
        })
        fig_funnel = px.funnel(sim_data, x='Count', y='Action', title="Simulation Engagement Funnel", 
                               color_discrete_sequence=[t['primary'], t['accent'], '#f59e0b', '#ef4444'])
        fig_funnel.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t['text']), height=350)
        st.plotly_chart(fig_funnel, use_container_width=True)

    with tab_alerts:
        st.subheader("High-Urgency Broadcast")
        alert_msg = st.text_area("Alert Content")
        if st.button("📢 Broadcast to All Devices"):
            st.success("Broadcast complete. Estimated reach: 14,200 devices.")

# --- FOOTER ---
if st.session_state.logged_in:
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 CampusShield | Institutional SOC")