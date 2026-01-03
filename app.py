import streamlit as st
import os
import pandas as pd
from datetime import datetime, date
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Page Config ---
st.set_page_config(page_title="TaxPilot", page_icon="💰", layout="wide")

# --- 2. NUCLEAR CSS (Aggressive Light Mode) ---
st.markdown("""
<style>
    /* 1. OVERRIDE STREAMLIT ROOT VARIABLES */
    /* This tells Streamlit to use these colors for everything */
    :root {
        --primary-color: #00C853;
        --background-color: #FFFFFF;
        --secondary-background-color: #F0F2F6;
        --text-color: #000000;
        --font: sans-serif;
    }

    /* 2. FORCE MAIN BACKGROUND & TEXT */
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* 3. FORCE SIDEBAR BACKGROUND */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E9ECEF;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label {
        color: #000000 !important; /* Force sidebar text black */
    }

    /* 4. FIX INPUT BOXES (The "Ghost Text" Fix) */
    /* Target every possible input type and force white bg + black text */
    input[type="text"], input[type="number"], .stTextInput input, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Fix for Chrome/Safari */
        caret-color: #000000 !important; /* Cursor color */
        border: 1px solid #CCCCCC !important;
    }
    
    /* Fix Selectbox/Dropdowns */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Fix Labels above inputs */
    label, .stTextInput label, .stNumberInput label, .stSelectbox label {
        color: #333333 !important;
    }

    /* 5. FIX METRIC CARDS */
    .stMetric {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        color: #000000 !important;
    }
    [data-testid="stMetricValue"] {
        color: #000000 !important; /* Force numbers black */
    }
    [data-testid="stMetricLabel"] {
        color: #666666 !important;
    }

    /* 6. BUTTONS */
    .stButton > button {
        background: linear-gradient(45deg, #00C853, #009688) !important;
        color: #FFFFFF !important; /* Keep button text white */
        border: none;
        font-weight: bold;
    }
    
    /* 7. HEADERS */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }

    /* Hide Defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar Navigation ---
st.sidebar.title("💰 TaxPilot")
st.sidebar.success("✅ Online")

# --- 4. API Key Setup ---
# PASTE YOUR KEY HERE
raw_api_key = "AIzaSyAJLhXLQaY4U-u6ipI_IFROXi_n1m5MAug"

my_key = raw_api_key.strip()
os.environ["GOOGLE_API_KEY"] = my_key

# Navigation
page = st.sidebar.radio("Navigate", ["🤖 AI Tax Assistant", "🧮 Smart Tax Estimator", "📅 Compliance Calendar"])

# --- 5. Main Logic ---

# ==========================
# 🤖 TAB 1: AI ASSISTANT
# ==========================
if page == "🤖 AI Tax Assistant":
    st.title("🤖 AI Tax Assistant")
    st.markdown("Your **Real-time Compliance Copilot**. Ask about GST, 44ADA, or Penalties.")
    
    user_query = st.text_input("Describe your situation (e.g., 'I am a freelance designer earning 15L...'):")
    
    if st.button("Ask Copilot"):
        if "PASTE" in my_key:
             st.error("❌ Please paste your API Key in app.py")
        elif not user_query:
            st.warning("⚠️ Please enter a question.")
        else:
            with st.spinner("Analyzing Latest Tax Rules (FY 2025-26)..."):
                try:
                    gemini_llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        verbose=True,
                        temperature=0.3,
                        google_api_key=my_key
                    )

                    tax_expert = Agent(
                        role='Compliance Expert',
                        goal='Simplify tax laws for micro-businesses and gig workers.',
                        backstory="You are an expert CA. You remove fear by explaining rules simply.",
                        verbose=True,
                        allow_delegation=False,
                        llm=gemini_llm 
                    )

                    answer_task = Task(
                        description=f"User Query: '{user_query}'. Provide a reassuring, accurate answer based on India FY 2025-26 laws.",
                        expected_output="Clear advice.",
                        agent=tax_expert
                    )

                    crew = Crew(agents=[tax_expert], tasks=[answer_task], verbose=True, memory=False)
                    result = crew.kickoff()
                    
                    st.success("✅ Advice Generated")
                    # Result Box: Light Grey bg, Dark Text
                    st.markdown(f"""
                    <div style="background-color: #F8F9FA; padding: 20px; border-radius: 10px; border-left: 5px solid #00C853; color: #333333;">
                        {result}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================
# 🧮 TAB 2: SMART ESTIMATOR
# ==========================
elif page == "🧮 Smart Tax Estimator":
    st.title("🧮 Smart Tax Estimator (FY 2025-26)")
    st.markdown("Calculate tax for **Micro-Businesses** & **Freelancers**.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Business Details")
        
        user_type = st.selectbox(
            "I am a...", 
            ["Freelancer / Professional", "Small Trader / Shopkeeper"]
        )
        st.session_state["user_type"] = user_type
        
        gross_income = st.number_input("Annual Revenue (₹)", min_value=0, step=50000, value=2000000)
        
        if user_type == "Freelancer / Professional":
            profit_rate = 0.50
            section_name = "Section 44ADA"
            desc = "As a professional, the govt assumes **50%** of your receipts are profit."
        else:
            profit_rate = 0.06 
            section_name = "Section 44AD"
            desc = "As a small trader (digital), the govt assumes only **6%** of your turnover is profit."

        # Info Box: Light green bg, dark text
        st.markdown(f"""
        <div style="background-color: #E8F5E9; padding: 10px; border-radius: 5px; border: 1px solid #C8E6C9; color: #1B5E20;">
            <strong>💡 {section_name} Logic:</strong><br>{desc}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("2. The Calculation")
        
        if user_type == "Small Trader / Shopkeeper":
            normal_profit = gross_income * 0.15 
        else:
            normal_profit = gross_income * 0.80 
            
        presumptive_profit = gross_income * profit_rate
        
        def calculate_tax(income):
            if income <= 300000: return 0
            tax = 0
            if income > 300000: tax += (min(income, 700000) - 300000) * 0.05
            if income > 700000: tax += (min(income, 1000000) - 700000) * 0.10
            if income > 1000000: tax += (min(income, 1200000) - 1000000) * 0.15
            if income > 1200000: tax += (min(income, 1500000) - 1200000) * 0.20
            if income > 1500000: tax += (income - 1500000) * 0.30
            if income <= 700000: return 0
            return tax * 1.04 

        tax_normal = calculate_tax(normal_profit)
        tax_presumptive = calculate_tax(presumptive_profit)
        savings = tax_normal - tax_presumptive

        c1, c2, c3 = st.columns(3)
        c1.metric("Regular Tax", f"₹{tax_normal:,.0f}")
        c2.metric(f"{section_name} Tax", f"₹{tax_presumptive:,.0f}", delta=f"-₹{savings:,.0f}", delta_color="inverse")
        c3.metric("You Save", f"₹{savings:,.0f}")

        chart_data = pd.DataFrame({
            "Regime": ["Regular Audit", f"Presumptive ({section_name})"],
            "Tax Payable": [tax_normal, tax_presumptive]
        })
        st.bar_chart(chart_data, x="Regime", y="Tax Payable", color="#00C853")

# ==========================
# 📅 TAB 3: PROACTIVE CALENDAR
# ==========================
elif page == "📅 Compliance Calendar":
    st.title("📅 Proactive Compliance Calendar")
    st.markdown("### 🛡️ Your Shield Against Penalties")
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Hackathon Demo Controls")
    simulated_date = st.sidebar.date_input("🕒 Simulate Today's Date", date(2026, 3, 1))
    st.caption(f"Current Simulation: **{simulated_date.strftime('%d %b %Y')}**")

    user_persona = st.session_state.get("user_type", "Freelancer / Professional")
    st.info(f"Viewing Timeline for: **{user_persona}** (Presumptive Scheme)")

    deadlines = [
        {"Event": "Advance Tax (100% Payment)", "Date": date(2026, 3, 15), "Type": "Money", "Why": "Avoid 1% interest.", "Penalty": "1% interest"},
        {"Event": "GST Return (QRMP Scheme)", "Date": date(2026, 3, 31), "Type": "Filing", "Why": "Quarterly return.", "Penalty": "Late fee"},
        {"Event": "ITR Filing (Form ITR-4)", "Date": date(2026, 7, 31), "Type": "Filing", "Why": "Final deadline.", "Penalty": "₹5,000 penalty"},
    ]

    upcoming_deadlines = [d for d in deadlines if d["Date"] >= simulated_date]
    upcoming_deadlines.sort(key=lambda x: x["Date"])

    if upcoming_deadlines:
        next_event = upcoming_deadlines[0]
        days_left = (next_event["Date"] - simulated_date).days
        
        if days_left <= 7:
            bg, border, txt, icon = "#FFEBEE", "#FFCDD2", "#C62828", "🚨"
        elif days_left <= 30:
            bg, border, txt, icon = "#FFFDE7", "#FFF9C4", "#F57F17", "⚠️"
        else:
            bg, border, txt, icon = "#E8F5E9", "#C8E6C9", "#2E7D32", "ℹ️"

        st.markdown(f"""
        <div style="padding: 20px; border-radius: 8px; background-color: {bg}; border: 1px solid {border}; color: {txt}; margin-bottom: 25px;">
            <h3 style="margin:0; color: {txt} !important;">{icon} {next_event['Event']}</h3>
            <p style="margin:5px 0 0 0; color: {txt} !important;">Due in <strong>{days_left} DAYS</strong>. {next_event['Why']}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: st.write(f"**Consequence:** {next_event['Why']}")
        with c2: st.button(f"Pay Now ➝", key="pay_btn")
        with c3: st.button("🔔 Remind Me", key="remind_btn")
            
        st.progress(max(0, 100 - (days_left * 3)))
    else:
        st.success("🎉 You are completely compliant! No upcoming deadlines.")

    st.markdown("### 🗓️ FY 2025-26 Compliance Roadmap")
    for item in deadlines:
        d_date = item["Date"]
        days_diff = (d_date - simulated_date).days
        status_text = "✅ Completed" if days_diff < 0 else f"📅 Due in {days_diff} days"
        
        with st.expander(f"{d_date.strftime('%d %b')} — {item['Event']}"):
            st.markdown(f"**Status:** {status_text}")
            st.markdown(f"**Risk:** {item['Penalty']}")
            st.button(f"Action: {item['Type']}", key=f"btn_{item['Event']}")

# Footer
st.markdown("---")
st.markdown("🏆 **Team Tech Titans**")