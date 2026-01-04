import streamlit as st
import os
import datetime
from datetime import date
import plotly.graph_objects as go
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_option_menu import option_menu 
from fpdf import FPDF
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TaxPilot", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INTELLIGENT TRACKING & STATE ---
if "user_actions" not in st.session_state:
    st.session_state["user_actions"] = {
        "visited_calendar": False,
        "used_ai": False,
        "calculated_tax": False
    }

if "prompt_input" not in st.session_state:
    st.session_state["prompt_input"] = ""

def get_compliance_score():
    base_score = 30
    actions = st.session_state["user_actions"]
    score = base_score
    if actions["visited_calendar"]: score += 10
    if actions["used_ai"]: score += 10
    if actions["calculated_tax"]: score += 42 
    if "user_role" in st.session_state: score += 10
    return min(score, 100)

# --- PDF GENERATOR FUNCTION ---
def create_pdf(revenue, expenses, tax_reg, tax_pres, savings, mode):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 10, txt="TaxPilot Estimate Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # Business Details
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Business Snapshot", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Annual Revenue: Rs. {revenue:,.0f}", ln=True)
    pdf.cell(200, 8, txt=f"Reported Expenses: Rs. {expenses:,.0f}", ln=True)
    pdf.ln(10)
    
    # Tax Liability
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Tax Liability Breakdown", ln=True)
    pdf.set_font("Arial", size=12)
    
    if mode == "Compare Both (Smart)":
        pdf.cell(200, 8, txt=f"Regular Tax Regime: Rs. {tax_reg:,.0f}", ln=True)
        pdf.cell(200, 8, txt=f"Presumptive Scheme (44AD/ADA): Rs. {tax_pres:,.0f}", ln=True)
        pdf.set_text_color(0, 150, 0)
        pdf.cell(200, 10, txt=f"Potential Savings: Rs. {savings:,.0f}", ln=True)
        pdf.set_text_color(0, 0, 0)
    else:
        val = tax_pres if mode == "Presumptive (Standard)" else tax_reg
        pdf.cell(200, 8, txt=f"Estimated Tax: Rs. {val:,.0f}", ln=True)

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="This is an AI-generated estimate. Please consult a CA before filing.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. PROFESSIONAL DARK UI STYLING ---
st.markdown("""
    <script src="https://unpkg.com/@phosphor-icons/web"></script>

    <style>
    /* 1. FORCE DARK BACKGROUNDS */
    :root {
        --bg-dark: #000000;
        --card-dark: #111111; 
        --text-main: #FFFFFF;
        --text-sub: #A0A0A0;
        --accent: #00C853;
    }

    html, body, .stApp {
        background-color: var(--bg-dark) !important;
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif;
    }

    /* 2. SIDEBAR SPECIFICS */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #222 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #111111 !important; 
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
    }

    /* 3. INPUTS & DROPDOWNS (CLOSED STATE) */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > div, 
    div[data-baseweb="input"] > div,
    textarea, 
    input[type="text"] {
        background-color: #262626 !important; 
        border: 1px solid #444 !important;
        color: white !important; 
        border-radius: 8px !important;
    }
    
    ::placeholder {
        color: #888 !important;
        opacity: 1;
    }

    /* 4. BUTTONS */
    .stButton > button {
        background: linear-gradient(180deg, #00E676 0%, #00C853 100%) !important;
        color: #000 !important;
        border: none;
        font-weight: 600;
    }

    /* 5. TEXT UTILITIES */
    h1, h2, h3, h4, p, span, div, li { color: #FFFFFF !important; }
    .stCaption, small { color: #888 !important; }
    
    .gradient-text {
        background: linear-gradient(90deg, #00C853, #B2FF59);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 6. STATUS BADGE */
    .status-badge {
        background: #0a1f0a;
        border: 1px solid #00C853;
        color: #00C853 !important;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* 7. HEADER FIX */
    header[data-testid="stHeader"] {
        background-color: #000000 !important;
    }
    header[data-testid="stHeader"] button {
        color: white !important;
    }

    /* 8. CALENDAR & POPOVER DEEP FIX */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"] {
        background-color: #111111 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        background-color: #111111 !important;
        color: #ccc !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #00C853 !important;
        color: black !important;
    }
    div[data-baseweb="calendar"] {
        background-color: #111111 !important;
        color: white !important;
    }
    div[data-baseweb="calendar"] button {
        color: white !important; 
    }
    div[data-baseweb="calendar"] div[aria-label^="Month"], 
    div[data-baseweb="calendar"] div[aria-label^="Year"] {
        color: white !important; 
        font-weight: bold !important;
    }
    div[data-baseweb="calendar"] div[role="grid"] div {
        color: #888 !important; 
    }
    div[data-baseweb="calendar"] button[role="gridcell"] {
        color: white !important; 
        background-color: transparent !important;
    }
    div[data-baseweb="calendar"] button[role="gridcell"]:hover {
        background-color: #333 !important;
        border-radius: 50% !important;
    }
    div[data-baseweb="calendar"] button[aria-selected="true"] {
        background-color: #00C853 !important;
        color: black !important;
        border-radius: 50% !important;
        font-weight: bold !important;
    }
    div[data-baseweb="calendar"] button[aria-label*="Today"] {
        border: 1px solid #00C853 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    # 1. Branding Area
    st.markdown("""
        <div style="margin-bottom: 25px; padding-left: 5px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #00C853, #009688); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    <i class="ph-bold ph-airplane-tilt" style="color: white; font-size: 24px;"></i>
                </div>
                <div>
                    <h2 style="margin:0; font-size: 20px; font-weight: 700; color: white !important;">TaxPilot</h2>
                    <p style="margin:0; font-size: 11px; color: #888 !important;">AI Compliance Suite</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. LANGUAGE SUPPORT
    with st.container(border=True):
        st.markdown("<p style='font-size: 11px; color: #666 !important; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;'>Language / भाषा</p>", unsafe_allow_html=True)
        selected_language = st.selectbox(
            "Select Language",
            ["English", "Hinglish", "Hindi", "Marathi"],
            label_visibility="collapsed"
        )

    # 3. Navigation
    with st.container(border=True):
        st.markdown("<p style='font-size: 11px; color: #666 !important; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px;'>Main Menu</p>", unsafe_allow_html=True)
        selected_page = option_menu(
            menu_title=None, 
            options=["AI Assistant", "Tax Estimator", "Calendar"], 
            icons=["robot", "calculator", "calendar-check"], 
            menu_icon="cast", 
            default_index=0, 
            key="nav_menu", 
            styles={
                "container": {"padding": "0!important", "background-color": "#111111"}, 
                "icon": {"color": "#00C853", "font-size": "16px"}, 
                "nav-link": {"color": "#ddd", "font-size": "14px", "margin": "4px 0", "background-color": "#111111"}, 
                "nav-link-selected": {"background-color": "rgba(0, 200, 83, 0.15)", "color": "#00C853", "border-left": "3px solid #00C853"}, 
            }
        )

    # 4. Financial Health & Schemes
    current_score = get_compliance_score()
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 14px; font-weight: 600; color: white !important;">Financial Health</span>
            <span style="color: #00C853 !important; font-weight: bold;">{current_score}</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(current_score)
        
        if current_score > 30:
            st.markdown("<hr style='margin: 10px 0; border-color: #333;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 10px; color: #888; text-transform: uppercase; font-weight: 700;'>Unlocked Benefits</p>", unsafe_allow_html=True)
            
            schemes = []
            role = st.session_state.get("user_role", "General")
            if "Freelancer" in role:
                schemes.append(("44ADA Scheme", "Save 50% Tax"))
                schemes.append(("Udyam Reg", "Cheap Loans"))
            else:
                schemes.append(("PM Mudra", "₹10L Loan"))
                schemes.append(("PM SVANidhi", "Street Vendor Loan"))
                
            for name, benefit in schemes:
                st.markdown(f"""
                <div style="margin-bottom: 6px; padding: 8px; background: #0a1f0a; border-left: 2px solid #00C853; border-radius: 4px;">
                    <div style="font-size: 12px; color: white; font-weight: 600;">{name}</div>
                    <div style="font-size: 10px; color: #aaa;">{benefit}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
             st.markdown("<p style='font-size: 11px; color: #888 !important; margin-top: 8px;'>Complete actions to unlock credit.</p>", unsafe_allow_html=True)

    # 5. Footer Status
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="status-badge">
            <div style="width: 6px; height: 6px; background: #00C853; border-radius: 50%; box-shadow: 0 0 8px #00C853;"></div>
            <span style="color: #00C853 !important;">SYSTEM OPERATIONAL</span>
        </div>
    """, unsafe_allow_html=True)

# --- 5. API KEY ---
try:
    # This grabs the key from Streamlit's secure storage
    my_key = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = my_key
except Exception:
    st.error("⚠️ API Key missing! Please add GOOGLE_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 6. PAGE LOGIC ---

# ==========================
# 🧮 TAB 2: SMART ESTIMATOR
# ==========================
if selected_page == "Tax Estimator":
    st.markdown('<h1 style="font-size: 3rem; margin-bottom: 10px;">Smart <span class="gradient-text">Estimator</span></h1>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 18px; color: #888 !important; margin-bottom: 40px;'>Compare regimes and calculate liability (FY 2025-26).</p>", unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 1.2], gap="large")

    with col_input:
        with st.container(border=True):
            st.markdown("### Business Details")
            
            user_type = st.selectbox(
                "I am a...", 
                ["Freelancer / Professional", "Small Trader / Shopkeeper"],
                key="user_role"
            )
            
            gross_income = st.number_input("Annual Revenue (₹)", min_value=0.0, step=50000.0, value=2000000.0, format="%.0f")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Calculation Mode**")
            calc_mode = st.radio(
                "Mode", 
                ["Presumptive (Standard)", "Regular (Actual Expenses)", "Compare Both (Smart)"], 
                label_visibility="collapsed"
            )

            total_expenses = 0.0
            if calc_mode in ["Regular (Actual Expenses)", "Compare Both (Smart)"]:
                st.info("💡 Tip: Enter valid business expenses to lower tax.")
                total_expenses = st.number_input("Total Annual Expenses (₹)", value=800000.0, step=10000.0, format="%.0f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            calculate_btn = st.button("Calculate Tax", type="primary", use_container_width=True)

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
            
            if calc_mode == "Compare Both (Smart)":
                if savings > 0:
                    st.markdown(f"""
                    <div style="background: rgba(0, 200, 83, 0.1); border: 1px solid #00C853; border-radius: 12px; padding: 30px; text-align: center;">
                        <h3 style="margin:0; color: #ccc !important; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Potential Savings</h3>
                        <h1 style="margin: 10px 0; font-size: 48px; color: #00C853 !important;">₹{savings:,.0f}</h1>
                        <p style="margin:0; color: #fff !important;">by choosing <b>{section_name}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No savings detected. Regular regime is better or equal.")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Regular Tax", f"₹{tax_regular:,.0f}")
                with c2:
                    st.metric(f"Presumptive ({section_name})", f"₹{tax_presumptive:,.0f}")

                fig = go.Figure(data=[
                    go.Bar(name='Regular', x=['Tax'], y=[tax_regular], marker_color='#FF5252'),
                    go.Bar(name='Presumptive', x=['Tax'], y=[tax_presumptive], marker_color='#00C853')
                ])
                fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)

            else:
                val = tax_presumptive if calc_mode == "Presumptive (Standard)" else tax_regular
                
                st.markdown(f"""
                <div style="background: #111; border: 1px solid #333; border-radius: 12px; padding: 40px; text-align: center;">
                    <h3 style="color: #888 !important;">Total Estimated Tax</h3>
                    <h1 style="font-size: 56px; color: #fff !important;">₹{val:,.0f}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            # --- PDF DOWNLOAD BUTTON ---
            pdf_data = create_pdf(gross_income, total_expenses, tax_regular, tax_presumptive, savings, calc_mode)
            st.download_button(
                label="📄 Download Official Report (PDF)",
                data=pdf_data,
                file_name=f"TaxPilot_Estimate_{datetime.date.today()}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        else:
            # --- PROFESSIONAL EMPTY STATE ---
            st.markdown("""
            <div style="
                background: linear-gradient(145deg, #111111, #0a0a0a);
                border: 1px solid #222;
                border-radius: 16px;
                padding: 80px 40px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            ">
                <div style="margin-bottom: 20px;">
                    <i class="ph-duotone ph-calculator" style="font-size: 64px; color: #00C853; opacity: 0.5;"></i>
                </div>
                <h2 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 600; color: #fff !important;">Ready to Estimate</h2>
                <p style="margin: 0; font-size: 14px; color: #888 !important; line-height: 1.5; max-width: 400px;">
                    Provide your business income and expenses on the left to unlock your personalized tax breakdown and savings analysis.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ==========================
# 🤖 TAB 1: AI ASSISTANT (DEFAULT)
# ==========================
elif selected_page == "AI Assistant":
    st.markdown('<h1 style="font-size: 3rem; margin-bottom: 10px;">AI <span class="gradient-text">Copilot</span></h1>', unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 18px; color: #888 !important; margin-bottom: 40px;'>Real-time regulatory intelligence in <b>{selected_language}</b>.</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1,2])
    
    # Dynamic Button Text based on Language
    btn_text_1 = "📉 Save Tax on 15L"
    btn_text_2 = "⚠️ GST Penalty?"
    
    if c1.button(btn_text_1): st.session_state["prompt_input"] = "I earn 15L. How to save tax?"
    if c2.button(btn_text_2): st.session_state["prompt_input"] = "What is the penalty for late GST?"

    user_query = st.text_input("Ask a question / प्रश्न पूछें:", value=st.session_state.get("prompt_input", ""))
    
    if st.button("🚀 Analyze / विश्लेषण करें", type="primary"):
        st.session_state["user_actions"]["used_ai"] = True
        
        if "PASTE" in my_key: st.error("API Key Missing")
        elif not user_query: st.warning("Enter a question.")
        else:
            with st.spinner("Consulting regulatory database..."):
                try:
                    # --- DYNAMIC AI PERSONA BASED ON LANGUAGE ---
                    
                    base_persona = """You are a top-tier Indian Chartered Accountant. 
                    You hate wall-of-text answers. 
                    You ALWAYS format your answers using Markdown Tables (for numbers) and Bullet points."""
                    
                    if selected_language == "Hinglish":
                        base_persona += """
                        IMPORTANT: Reply in a mix of Hindi and English (Latin script) so a layman can understand.
                        Example: "Haan, aap 44ADA scheme use kar sakte hain agar aapki income 75L se kam hai."
                        Keep technical terms (like 'Deduction', 'Section 80C') in English.
                        """
                    elif selected_language == "Hindi":
                        base_persona += """
                        IMPORTANT: Reply in PURE HINDI (Devanagari Script).
                        Example: "जी हाँ, आप 44ADA योजना का उपयोग कर सकते हैं।"
                        Keep technical terms in English brackets like 'Income Tax Return (ITR)'.
                        """
                    elif selected_language == "Marathi":
                        base_persona += """
                        IMPORTANT: Reply in MARATHI (Marathi Script).
                        Explain simply. Keep technical tax terms in English brackets like 'Income Tax Return (ITR)'.
                        """
                    else:
                        base_persona += "Reply in professional, clear English."

                    # Initialize Agent
                    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=my_key, temperature=0.3)
                    agent = Agent(
                        role='Senior Tax Consultant', 
                        goal='Provide precise, formatted tax advice.', 
                        backstory=base_persona, 
                        llm=llm
                    )
                    
                    task = Task(
                        description=user_query, 
                        expected_output="A structured markdown response with tables and bullet points.", 
                        agent=agent
                    )
                    
                    crew = Crew(agents=[agent], tasks=[task])
                    res = crew.kickoff()
                    
                    # --- DISPLAY RESULTS (Pure Markdown) ---
                    st.markdown("---")
                    with st.container(border=True):
                        st.markdown("""
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                            <div style="width: 30px; height: 30px; background: rgba(0,200,83,0.2); border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                                <i class="ph-bold ph-sparkle" style="color: #00C853;"></i>
                            </div>
                            <h4 style="margin:0; color: white !important;">Expert Insight</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Direct Markdown Render for Tables/Lists
                        st.markdown(res)
                        
                except Exception as e: st.error(f"AI Error: {e}")

# ==========================
# 📅 TAB 3: CALENDAR
# ==========================
elif selected_page == "Calendar":
    st.markdown('<h1 style="font-size: 3rem; margin-bottom: 10px;">Proactive <span class="gradient-text">Compliance</span></h1>', unsafe_allow_html=True)
    
    # Simple Date Simulation
    with st.container(border=True):
         st.markdown("### ⏱️ Time Machine")
         simulated_today = st.date_input("Simulate Today as:", date(2026, 3, 1))
    
    deadline_date = date(2026, 3, 15)
    days_left = (deadline_date - simulated_today).days
    
    # Progress
    fy_start = date(2025, 4, 1)
    fy_end = date(2026, 3, 31)
    total = (fy_end - fy_start).days
    passed = (simulated_today - fy_start).days
    progress = max(0.0, min(1.0, passed / total))

    # Dynamic Alert
    if days_left < 7:
        color = "#FF5252"
        title = "URGENT DUE"
        msg = f"Tax payment due in {days_left} days."
    elif days_left < 30:
        color = "#FF9800"
        title = "Advance Tax Due"
        msg = f"Deadline approaching in {days_left} days."
    else:
        color = "#00C853"
        title = "On Track"
        msg = f"Next deadline in {days_left} days."

    st.markdown(f"""
    <div style="background: {color}15; border-left: 4px solid {color}; border-radius: 4px; padding: 20px; margin-bottom: 25px;">
        <h3 style="color: {color} !important; margin:0; font-size: 18px;">{title}</h3>
        <p style="color: #ccc !important; margin: 5px 0 0 0;">{msg}</p>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress, text="FY 2025-26 Timeline")
    
    events = [
        {"d": "15 Mar", "t": "Advance Tax (Final)", "sub": "100% liability due"},
        {"d": "31 Mar", "t": "GST Return", "sub": "QRMP Scheme"},
        {"d": "31 Jul", "t": "ITR Filing", "sub": "Individual / Non-audit"}
    ]

    st.markdown("### Upcoming Events")
    for e in events:
        with st.expander(f"{e['d']} — {e['t']}"):
            st.write(e['sub'])
            st.button("Mark Complete", key=e['t'])
            st.session_state["user_actions"]["visited_calendar"] = True