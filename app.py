import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_option_menu import option_menu 

# --- 1. Page Config ---
st.set_page_config(
    page_title="TaxPilot", 
    page_icon="👨‍✈️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PREMIUM DARK MODE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #050505 !important; 
        color: #E0E0E0 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid #1F2937;
    }
    header[data-testid="stHeader"] {
        background-color: #050505 !important;
    }
    h1, h2, h3 {
        color: #FFFFFF !important;
        text-shadow: 0 0 10px rgba(0, 200, 83, 0.4); 
        font-weight: 800 !important;
    }
    .stMetric {
        background-color: #111111 !important;
        border: 1px solid #333333 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #FFFFFF !important;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #161B22 !important; 
        color: #E0E0E0 !important;
        border: 1px solid #30363D !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #00C853, #009688) !important;
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INIT (For Dynamic Health Bar) ---
if "compliance_score" not in st.session_state:
    st.session_state["compliance_score"] = 40  # Start Red
if "loan_unlocked" not in st.session_state:
    st.session_state["loan_unlocked"] = False

# --- 4. Sidebar Navigation & Features ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2917/2917242.png", width=70) 
    st.title("TaxPilot")
    st.caption("AI Tax & Compliance for India")
    
    st.markdown("---")

    selected_page = option_menu(
        menu_title=None, 
        options=["AI Assistant", "Tax Estimator", "Calendar"], 
        icons=["robot", "calculator", "calendar-check"], 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00C853", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "5px", "color": "#E0E0E0"},
            "nav-link-selected": {"background-color": "#1F2937", "color": "#00C853", "font-weight": "bold", "border-left": "5px solid #00C853"}, 
        }
    )

    st.markdown("---")
    
    # === DYNAMIC FINANCIAL HEALTH WIDGET ===
    st.markdown("### 💳 Financial Health")
    
    current_score = st.session_state["compliance_score"]
    
    if current_score < 50:
        bar_color = "red"
        msg = "⚠️ Risk: High"
    elif current_score < 80:
        bar_color = "yellow"
        msg = "⚠️ Improve Score"
    else:
        bar_color = "green"
        msg = "✅ Excellent"

    st.write(f"**Score:** {current_score}/100")
    st.progress(current_score)
    st.caption(msg)
    
    if st.session_state["loan_unlocked"]:
        st.success("✅ **Eligible: Mudra Loan (₹5L)**")
    else:
        st.error("🔒 **Loan Locked** (File Tax to Unlock)")
        
    st.markdown("---")
    language = st.selectbox("🗣️ Language", ["English", "Hindi", "Marathi"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0, 200, 83, 0.1); border: 1px solid #00C853; border-radius: 6px; padding: 10px; display: flex; align-items: center; gap: 10px;">
        <div style="width: 10px; height: 10px; background: #00C853; border-radius: 50%; box-shadow: 0 0 10px #00C853;"></div>
        <span style="color: #00C853; font-weight: 600; font-size: 14px;">System Online</span>
    </div>
    """, unsafe_allow_html=True)

# --- 5. API Key Setup ---
raw_api_key = "AIzaSyAJLhXLQaY4U-u6ipI_IFROXi_n1m5MAug" 
my_key = raw_api_key.strip()
os.environ["GOOGLE_API_KEY"] = my_key

# --- 6. Main Logic ---

# ==========================
# 🤖 TAB 1: AI ASSISTANT
# ==========================
if selected_page == "AI Assistant":
    st.title("🤖 AI Tax Assistant")
    st.markdown("Your **Real-time Compliance Copilot**. Ask about GST, 44ADA, or Penalties.")
    st.markdown("---")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    if col_p1.button("📉 Save Tax on 15L"): st.session_state["prompt_input"] = "I am a freelancer earning 15 Lakhs. How can I save tax?"
    if col_p2.button("🧾 What is 44ADA?"): st.session_state["prompt_input"] = "Explain Section 44ADA in simple terms."
    if col_p3.button("⚠️ GST Penalty Limits"): st.session_state["prompt_input"] = "What is the penalty for late GST filing?"

    default_prompt = st.session_state.get("prompt_input", "")
    user_query = st.text_input("Describe your situation:", value=default_prompt)
    
    if st.button("🚀 Ask Copilot"):
        if "PASTE" in my_key: st.error("❌ API Key Missing")
        elif not user_query: st.warning("⚠️ Enter a question.")
        else:
            with st.spinner(f"Analyzing..."):
                try:
                    gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, google_api_key=my_key)
                    tax_expert = Agent(role='Expert', goal='Simplify tax.', backstory="Expert CA.", llm=gemini_llm)
                    task = Task(description=f"Query: {user_query}. Answer in {language} bullet points.", expected_output="Advice.", agent=tax_expert)
                    crew = Crew(agents=[tax_expert], tasks=[task], verbose=True)
                    result = crew.kickoff()
                    st.success("✅ Advice Generated")
                    st.markdown(f'<div style="background-color:#111827;padding:20px;border-radius:10px;border-left:5px solid #00C853;">{result}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Error: {e}")

# ==========================
# 🧮 TAB 2: SMART ESTIMATOR (Updated Logic)
# ==========================
elif selected_page == "Tax Estimator":
    st.title("🧮 Smart Tax Estimator")
    st.markdown("Calculate tax based on your preferred regime.")
    st.markdown("---")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Business Details")
        
        # 1. Basic Inputs
        user_type = st.selectbox("I am a...", ["Freelancer / Professional", "Small Trader / Shopkeeper"])
        gross_income = st.number_input("Annual Revenue (₹)", min_value=0.0, step=50000.0, value=2000000.0, format="%.0f")

        # 2. Select Mode (Logic Fix)
        st.write("")
        st.markdown("**⚙️ Select Calculation Mode:**")
        calc_mode = st.radio(
            "Mode",
            ["Presumptive (Standard)", "Regular (Actual Expenses)", "Compare Both (Smart)"],
            horizontal=True,
            label_visibility="collapsed"
        )

        # 3. Dynamic Expense Input (Only shows if Regular or Compare is selected)
        total_expenses = 0.0
        if calc_mode in ["Regular (Actual Expenses)", "Compare Both (Smart)"]:
            st.markdown("---")
            st.markdown(f"**📉 Deduction of Expenses:**")
            total_expenses = st.number_input(
                "Total Business Expenses (Rent, Salary, Internet, etc.)", 
                min_value=0.0, 
                max_value=gross_income, 
                step=10000.0, 
                value=800000.0, 
                format="%.0f",
                help="Enter actual expenses to calculate Net Profit for Regular Tax."
            )
            actual_profit = gross_income - total_expenses
            st.caption(f"📈 Your Actual Net Profit: ₹{actual_profit:,.0f}")
        
        # Determine Presumptive Rates
        if user_type == "Freelancer / Professional":
            profit_rate = 0.50
            section_name = "Section 44ADA"
        else:
            profit_rate = 0.06
            section_name = "Section 44AD"
            
        calculate_btn = st.button("🚀 Calculate Tax", type="primary")

    with col2:
        st.subheader("2. Tax Analysis")
        
        # Trigger Score Update on Click
        if calculate_btn:
            st.session_state["compliance_score"] = 92
            st.session_state["loan_unlocked"] = True
            st.rerun()

        # === CALCULATION LOGIC ===
        def get_tax(income):
            if income <= 300000: return 0
            tax = 0
            if income > 300000: tax += (min(income, 700000) - 300000) * 0.05
            if income > 700000: tax += (min(income, 1000000) - 700000) * 0.10
            if income > 1000000: tax += (min(income, 1200000) - 1000000) * 0.15
            if income > 1200000: tax += (min(income, 1500000) - 1200000) * 0.20
            if income > 1500000: tax += (income - 1500000) * 0.30
            return tax * 1.04 

        # 1. Presumptive Math
        presumptive_profit = gross_income * profit_rate
        tax_presumptive = get_tax(presumptive_profit)

        # 2. Regular Math (Only if expenses provided)
        tax_regular = 0
        if calc_mode != "Presumptive (Standard)":
            tax_regular = get_tax(gross_income - total_expenses)

        # === DISPLAY LOGIC ===
        
        # SCENARIO A: PRESUMPTIVE ONLY
        if calc_mode == "Presumptive (Standard)":
            st.metric(f"{section_name} Tax", f"₹{tax_presumptive:,.0f}", help=f"Calculated on flat {profit_rate*100}% profit")
            st.info(f"💡 **Why this?** No need to maintain expense books. Govt assumes flat profit.")

        # SCENARIO B: REGULAR ONLY
        elif calc_mode == "Regular (Actual Expenses)":
            st.metric("Regular Tax (Audit)", f"₹{tax_regular:,.0f}", help=f"Calculated on Profit: ₹{(gross_income-total_expenses):,.0f}")
            st.info(f"💡 **Why this?** Good if your actual profit is VERY low (high expenses). Requires bookkeeping.")

        # SCENARIO C: COMPARE BOTH
        else:
            savings = tax_regular - tax_presumptive
            c1, c2, c3 = st.columns(3)
            
            c1.metric("Regular", f"₹{tax_regular:,.0f}")
            c2.metric("Presumptive", f"₹{tax_presumptive:,.0f}")
            
            if savings > 0:
                c3.metric("You Save", f"₹{savings:,.0f}", delta="Best Choice")
                st.success(f"✅ Recommendation: **{section_name}** is better.")
            elif savings < 0:
                diff = abs(savings)
                c3.metric("You Save", f"₹{diff:,.0f}", delta="Regular is Better")
                st.warning(f"⚠️ Recommendation: **Regular Tax** is better because your expenses are high.")
            else:
                c3.metric("Diff", "₹0")

            # Chart for Comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(x=['Regular'], y=[tax_regular], marker=dict(color='#374151')))
            fig.add_trace(go.Bar(x=['Presumptive'], y=[tax_presumptive], marker=dict(color='#00C853')))
            fig.update_layout(height=250, margin=dict(t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        # Download Report
        report_text = f"Tax Analysis\nMode: {calc_mode}\nRegular Tax: {tax_regular}\nPresumptive Tax: {tax_presumptive}"
        st.download_button("📄 Download Report", report_text, "tax_summary.txt")

# ==========================
# 📅 TAB 3: CALENDAR
# ==========================
elif selected_page == "Calendar":
    st.title("📅 Compliance Calendar")
    st.markdown("### 🛡️ Your Shield Against Penalties")
    
    # If they visit calendar, bump score slightly if it's not already high
    if st.session_state["compliance_score"] < 50:
        st.session_state["compliance_score"] = 60
        st.rerun()

    deadlines = [
        {"Event": "Advance Tax", "Date": date(2026, 3, 15), "Type": "Payment", "Why": "Avoid Interest"},
        {"Event": "GST Return", "Date": date(2026, 3, 31), "Type": "Filing", "Why": "QRMP Filing"},
        {"Event": "ITR Filing", "Date": date(2026, 7, 31), "Type": "Filing", "Why": "Final Date"},
    ]
    
    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        for item in deadlines:
            with st.expander(f"{item['Date']} — {item['Event']}"):
                st.write(f"**Why:** {item['Why']}")
                st.button(f"Action: {item['Event']}", key=item['Event'])

st.markdown("---")
st.markdown("🏆 **Team Tech Titans** | Built for Hackathon 2026")