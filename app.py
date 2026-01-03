import streamlit as st
import os
import datetime
from datetime import date
import plotly.graph_objects as go
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_option_menu import option_menu 

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TaxPilot", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INTELLIGENT TRACKING SYSTEM ---
if "user_actions" not in st.session_state:
    st.session_state["user_actions"] = {
        "visited_calendar": False,
        "used_ai": False,
        "calculated_tax": False
    }

def get_compliance_score():
    base_score = 30
    actions = st.session_state["user_actions"]
    score = base_score
    if actions["visited_calendar"]: score += 10
    if actions["used_ai"]: score += 10
    if actions["calculated_tax"]: score += 42 
    if "user_role" in st.session_state: score += 10
    return min(score, 100)

# --- 3. ULTIMATE DARK MODE & BOLD WHITE BORDERS ---
st.markdown("""
    <script src="https://unpkg.com/@phosphor-icons/web"></script>

    <style>
    /* 1. GLOBAL RESET */
    :root {
        --primary-color: #00C853;
        --background-color: #000000;
        --secondary-background-color: #050505;
        --text-color: #FFFFFF;
        --font: "sans-serif";
    }

    html, body, .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    /* 2. TEXT VISIBILITY */
    h1, h2, h3, h4, h5, h6, p, li, span, div, label {
        color: #FFFFFF !important;
    }
    
    .stCaption, small {
        color: #E0E0E0 !important;
    }

    /* 3. BOLD WHITE INPUT BORDERS */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > div,
    input.st-bd {
        background-color: #111111 !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    input {
        color: #FFFFFF !important;
    }

    /* Fix for Date Input in Sidebar */
    div[data-baseweb="input"] > div {
        background-color: #111111 !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 8px !important;
    }

    /* 4. DROPDOWN MENU */
    div[data-baseweb="popover"] {
        background-color: #111111 !important;
        border: 2px solid #FFFFFF !important;
    }

    div[data-baseweb="popover"] ul {
        background-color: #111111 !important;
    }

    div[data-baseweb="popover"] li {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-bottom: 1px solid #333 !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #00C853 !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="select"] svg {
        fill: #FFFFFF !important;
    }

    /* 5. SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid #FFFFFF !important; 
    }
    
    /* Target the native Streamlit container in sidebar to look like our card */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }

    header[data-testid="stHeader"] { background-color: transparent !important; }

    /* 6. BOLD WHITE CARD STYLES */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid #FFFFFF !important; 
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .empty-state {
        background: rgba(255, 255, 255, 0.02);
        border: 2px dashed #FFFFFF !important;
        border-radius: 16px;
        text-align: center;
        padding: 60px 20px;
    }

    /* 7. BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #00C853 0%, #009688 100%) !important;
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }

    .gradient-text {
        background: linear-gradient(45deg, #00C853, #69F0AE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    h1 .gradient-text {
       color: transparent !important; 
    }

    .icon-xl { font-size: 32px; vertical-align: middle; margin-right: 10px; color: #00C853 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    # 1. Header
    st.markdown("""
        <div style="border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
            <i class="ph-fill ph-circles-three-plus" style="font-size: 28px; color: #00C853;"></i>
            <div>
                <h2 style="margin:0; font-size: 22px; color: white !important;">TaxPilot</h2>
                <small style="color: #888; font-size: 10px;">AI Tax & Compliance</small>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Menu
    selected_page = option_menu(
        menu_title=None, 
        options=["AI Assistant", "Tax Estimator", "Calendar"], 
        icons=["robot", "calculator", "calendar-check"], 
        menu_icon="cast", 
        default_index=1,
        key="nav_menu", 
        styles={
            "container": {"padding": "0!important", "background-color": "#000000"},
            "icon": {"color": "#00C853", "font-size": "18px"}, 
            "nav-link": {"color": "#FFFFFF", "font-size": "16px", "margin": "8px 0", "background-color": "#000000"},
            "nav-link-selected": {"background-color": "rgba(0, 200, 83, 0.1)", "color": "#00C853", "border": "3px solid #FFFFFF", "border-radius": "8px"}, 
        }
    )

    # 3. CONDITIONAL DATE PICKER (Only shows if Calendar is selected)
    simulated_today = date(2026, 3, 1) # Default
    
    if selected_page == "Calendar":
        st.markdown("---") # Simple separator
        st.caption("📅 Simulation Date")
        # Ensure we use date(2026, 3, 1) as a default anchor
        simulated_today = st.date_input(
            "Current Date", 
            date(2026, 3, 1), 
            key="calendar_date_picker",
            label_visibility="collapsed"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Financial Health Widget (Fixed: No ghost box!)
    current_score = get_compliance_score()
    
    # We use st.container(border=True) which we styled with CSS above
    with st.container(border=True):
        st.markdown("### <i class='ph ph-heartbeat'></i> Financial Health", unsafe_allow_html=True)
        st.write(f"**Score:** {current_score}/100")
        st.progress(current_score)
        
        if current_score > 80:
            role = st.session_state.get("user_role", "Small Trader / Shopkeeper")
            if "Freelancer" in role:
                loan_name = "Business Credit"
                amount = "₹2,00,000"
                icon = "ph-credit-card"
            else:
                loan_name = "Mudra Loan"
                amount = "₹5,00,000"
                icon = "ph-bank"
            
            st.markdown(f"""
            <div style="margin-top: 10px; padding: 10px; background: rgba(0, 200, 83, 0.1); border-radius: 8px; border: 1px solid #00C853;">
                <div style="font-weight: bold; color: #00C853; font-size: 14px;">✅ Eligible: {loan_name}</div>
                <div style="font-size: 12px; color: #ddd; margin-top: 4px;"><i class="ph {icon}"></i> Limit: {amount}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("⚠️ Complete actions to unlock credit.")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 5. System Status
    st.markdown("""
    <div style="border: 1px solid #333; border-radius: 6px; padding: 10px; display: flex; align-items: center; gap: 10px;">
        <div style="width: 8px; height: 8px; background: #00C853; border-radius: 50%; box-shadow: 0 0 10px #00C853;"></div>
        <span style="color: #888 !important; font-weight: 500; font-size: 11px;">SYSTEM OPERATIONAL</span>
    </div>
    """, unsafe_allow_html=True)

# --- 5. API KEY ---
raw_api_key = "AIzaSyAJLhXLQaY4U-u6ipI_IFROXi_n1m5MAug" 
my_key = raw_api_key.strip()
os.environ["GOOGLE_API_KEY"] = my_key

# --- 6. PAGE LOGIC ---

# ==========================
# 🤖 TAB 1: AI ASSISTANT
# ==========================
if selected_page == "AI Assistant":
    st.markdown('<h1 style="font-size: 3rem;"><i class="ph ph-sparkle icon-xl"></i> AI <span class="gradient-text" style="color:transparent !important;">Copilot</span></h1>', unsafe_allow_html=True)
    st.markdown("Your **Real-time Compliance Expert**.")
    st.write("")
    
    c1, c2, c3 = st.columns([1,1,2])
    if c1.button("📉 Save Tax on 15L"): st.session_state["prompt_input"] = "I earn 15L. How to save tax?"
    if c2.button("⚠️ GST Penalty?"): st.session_state["prompt_input"] = "What is the penalty for late GST?"

    user_query = st.text_input("Ask a question:", value=st.session_state.get("prompt_input", ""))
    
    if st.button("🚀 Ask Copilot"):
        st.session_state["user_actions"]["used_ai"] = True
        
        if "PASTE" in my_key: st.error("API Key Missing")
        elif not user_query: st.warning("Enter a question.")
        else:
            with st.spinner("Analyzing regulations..."):
                try:
                    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=my_key)
                    agent = Agent(role='Expert', goal='Help user', backstory='Expert', llm=llm)
                    task = Task(description=user_query, expected_output="Short answer", agent=agent)
                    crew = Crew(agents=[agent], tasks=[task])
                    res = crew.kickoff()
                    
                    st.markdown(f"""
                    <div class="glass-card">
                        <h3><i class="ph ph-lightbulb"></i> Expert Advice</h3>
                        <p style="margin-top: 10px; line-height: 1.6; color: white;">{res}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.toast("Score Updated: Learning (+10)", icon="📈")
                except: st.error("AI Error")

# ==========================
# 🧮 TAB 2: SMART ESTIMATOR
# ==========================
elif selected_page == "Tax Estimator":
    st.markdown('<h1 style="font-size: 3rem;"><i class="ph ph-calculator icon-xl"></i> Smart <span class="gradient-text" style="color:transparent !important;">Estimator</span></h1>', unsafe_allow_html=True)
    st.markdown("Compare regimes and calculate liability with precision **(FY 2025-26)**.")
    st.write("") 

    col_input, col_result = st.columns([1, 1.2], gap="large")

    with col_input:
        with st.container(border=True):
            st.markdown("### <i class='ph ph-briefcase'></i> Business Details", unsafe_allow_html=True)
            
            user_type = st.selectbox(
                "I am a...", 
                ["Freelancer / Professional", "Small Trader / Shopkeeper"],
                key="user_role"
            )
            
            gross_income = st.number_input("Annual Revenue (₹)", min_value=0.0, step=50000.0, value=2000000.0, format="%.0f")

            st.write("")
            st.markdown("**Calculation Mode**")
            calc_mode = st.radio(
                "Mode", 
                ["Presumptive (Standard)", "Regular (Actual Expenses)", "Compare Both (Smart)"], 
                label_visibility="collapsed"
            )

            total_expenses = 0.0
            if calc_mode in ["Regular (Actual Expenses)", "Compare Both (Smart)"]:
                st.info("Entering expenses helps compare regimes!")
                total_expenses = st.number_input("Total Annual Expenses (₹)", value=800000.0, step=10000.0, format="%.0f")
            
            st.write("")
            calculate_btn = st.button("🚀 Calculate Tax", type="primary", use_container_width=True)

    with col_result:
        profit_rate = 0.50 if "Freelancer" in user_type else 0.06
        section_name = "Section 44ADA" if "Freelancer" in user_type else "Section 44AD"
        
        # --- Tax Logic ---
        def get_tax(inc):
            if inc <= 1200000: return 0
            tax = 0
            if inc > 400000: tax += (min(inc, 800000) - 400000) * 0.05
            if inc > 800000: tax += (min(inc, 1200000) - 800000) * 0.10
            if inc > 1200000: tax += (min(inc, 1600000) - 1200000) * 0.15
            if inc > 1600000: tax += (min(inc, 2000000) - 1600000) * 0.20
            if inc > 2000000: tax += (min(inc, 2400000) - 2000000) * 0.25
            if inc > 2400000: tax += (inc - 2400000) * 0.30
            excess_income = inc - 1200000
            if tax > excess_income: tax = excess_income
            return tax * 1.04

        presumptive_profit = gross_income * profit_rate
        tax_presumptive = get_tax(presumptive_profit)
        tax_regular = get_tax(gross_income - total_expenses) if calc_mode != "Presumptive (Standard)" else 0
        savings = tax_regular - tax_presumptive

        if calculate_btn:
            st.session_state["user_actions"]["calculated_tax"] = True
            st.markdown("### <i class='ph ph-chart-pie-slice'></i> Tax Analysis", unsafe_allow_html=True)
            
            if calc_mode == "Compare Both (Smart)":
                if savings > 0:
                    st.markdown(f"""
                    <div class="glass-card" style="background: rgba(0, 200, 83, 0.1); border-color: #00C853 !important; text-align: center;">
                        <h3 style="margin:0; color: #E0E0E0 !important; font-size: 1rem;">🎉 YOU SAVE</h3>
                        <h1 style="margin:0; font-size: 3rem; color: #00C853 !important;">₹{savings:,.0f}</h1>
                        <p style="margin:0; opacity: 0.8; color: white !important;">by choosing {section_name} (Presumptive)</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif savings < 0:
                     st.markdown(f"""
                    <div class="glass-card" style="background: rgba(255, 82, 82, 0.1); border-color: #FF5252 !important; text-align: center;">
                        <h3 style="margin:0; color: #E0E0E0 !important; font-size: 1rem;">⚠️ BETTER OPTION</h3>
                        <h1 style="margin:0; font-size: 2rem; color: #FF5252 !important;">Regular Tax Regime</h1>
                        <p style="margin:0; opacity: 0.8; color: white !important;">Presumptive is expensive by ₹{abs(savings):,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Both regimes result in the same tax liability.")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""<div class="glass-card" style="text-align: center;"><small style="color:#ddd;">Regular Tax</small><h3 style="color: #FF5252 !important;">₹{tax_regular:,.0f}</h3></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="glass-card" style="text-align: center;"><small style="color:#ddd;">{section_name}</small><h3 style="color: #00C853 !important;">₹{tax_presumptive:,.0f}</h3></div>""", unsafe_allow_html=True)

                st.markdown("#### Visual Comparison")
                fig = go.Figure(data=[
                    go.Bar(name='Regular', x=['Tax'], y=[tax_regular], marker_color='#FF5252'),
                    go.Bar(name='Presumptive', x=['Tax'], y=[tax_presumptive], marker_color='#00C853')
                ])
                fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)

            else:
                val = tax_presumptive if calc_mode == "Presumptive (Standard)" else tax_regular
                st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <h3 style="margin:0; color: #E0E0E0 !important;">Estimated Tax Liability</h3>
                    <h1 style="margin:0; font-size: 3.5rem; color: #69F0AE !important;">₹{val:,.0f}</h1>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <i class="ph ph-trend-up" style="font-size: 40px; color: #888; margin-bottom: 15px;"></i>
                <h3 style="color: #FFFFFF; margin-bottom: 10px;">Ready to Optimize?</h3>
                <p style="color: #E0E0E0; font-size: 14px; max-width: 300px; margin: 0 auto;">
                    Fill in your business details on the left. We'll instantly compare regimes and find your savings.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ==========================
# 📅 TAB 3: CALENDAR (PROACTIVE)
# ==========================
elif selected_page == "Calendar":
    if not st.session_state["user_actions"]["visited_calendar"]:
        st.session_state["user_actions"]["visited_calendar"] = True
        st.toast("Score Updated: Awareness (+10)", icon="📅")
    
    st.markdown('<h1 style="font-size: 3rem;"><i class="ph ph-calendar-check icon-xl"></i> Proactive <span class="gradient-text" style="color:transparent !important;">Compliance</span></h1>', unsafe_allow_html=True)
    
    # --- DYNAMIC DATE LOGIC ---
    deadline_date = date(2026, 3, 15)
    days_left = (deadline_date - simulated_today).days
    
    # Progress Logic (FY 2025-26: Apr 1 2025 to Mar 31 2026)
    fy_start = date(2025, 4, 1)
    fy_end = date(2026, 3, 31)
    total_fy_days = (fy_end - fy_start).days
    days_passed = (simulated_today - fy_start).days
    progress_ratio = max(0.0, min(1.0, days_passed / total_fy_days))

    # Alert Styling based on urgency
    if days_left < 0:
        alert_color = "#FF5252" # Red
        alert_title = "OVERDUE"
        alert_desc = f"You are late by {abs(days_left)} days. Interest applies."
        bg_color = "rgba(255, 82, 82, 0.1)"
    elif days_left < 7:
        alert_color = "#FF5252" # Red (Urgent)
        alert_title = "URGENT ATTENTION"
        alert_desc = f"Due in <b>{days_left} DAYS</b> (15th March). Act fast."
        bg_color = "rgba(255, 82, 82, 0.1)"
    elif days_left < 30:
        alert_color = "#FF9800" # Orange
        alert_title = "Advance Tax (100% Payment)"
        alert_desc = f"Due in <b>{days_left} DAYS</b> (15th March). Avoid 1% monthly interest."
        bg_color = "rgba(255, 152, 0, 0.1)"
    else:
        alert_color = "#00C853" # Green
        alert_title = "Compliance on Track"
        alert_desc = f"Next deadline is in <b>{days_left} days</b>."
        bg_color = "rgba(0, 200, 83, 0.1)"

    role = st.session_state.get("user_role", "Freelancer / Professional")
    st.info(f"Viewing Timeline for: **{role}** (Presumptive Scheme)")

    # DYNAMIC ALERT BOX
    st.markdown(f"""
    <div style="background: {bg_color}; border: 1px solid {alert_color}; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <h3 style="color: {alert_color} !important; margin:0; display:flex; align-items:center; gap:8px;">
            <i class="ph-fill ph-warning-circle"></i> {alert_title}
        </h3>
        <p style="color: #FFFFFF !important; margin: 5px 0;">{alert_desc}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        st.button("💳 Pay Now", type="primary", use_container_width=True)
    with c2:
        st.button("🔔 Remind Me", use_container_width=True)

    st.write("")
    
    # DYNAMIC PROGRESS BAR
    st.progress(progress_ratio, text=f"FY 2025-26 Progress: {int(progress_ratio*100)}%")
    st.caption(f"Current Date Simulation: {simulated_today.strftime('%d %b %Y')}")
    st.write("")

    st.markdown("#### <i class='ph ph-list-checks'></i> Upcoming Events", unsafe_allow_html=True)
    
    events = [
        {"date": "15 Mar", "title": "Advance Tax (Installment 4)", "desc": "Mandatory if tax liability > ₹10k"},
        {"date": "31 Mar", "title": "GST Return (QRMP)", "desc": "Quarterly return for small taxpayers"},
        {"date": "31 Jul", "title": "Income Tax Return (ITR)", "desc": "File ITR-3 or ITR-4 to claim refunds"},
    ]

    for event in events:
        with st.expander(f"{event['date']} — {event['title']}"):
            st.write(event['desc'])
            if st.button(f"Mark Done: {event['title']}", key=event['title']):
                st.success("MARKED AS DONE")

st.markdown("---")
st.caption("🏆 **Team Tech Titans** | Built for Hackathon 2026")