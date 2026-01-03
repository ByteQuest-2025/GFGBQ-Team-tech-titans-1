import streamlit as st
import os
import pandas as pd
from datetime import datetime, date
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Page Config ---
st.set_page_config(page_title="TaxPilot", page_icon="💰", layout="wide")

# Custom CSS to make it look like a "Winning" Product
# ADDED: Specific font-size reduction for metric values to fit large numbers
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stMetric { background-color: #0E1117; border: 1px solid #303030; padding: 10px; border-radius: 5px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    
    /* FIX: Reduce font size of the numbers so Crores fit in the box */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. Sidebar Navigation ---
st.sidebar.title("💰 TaxPilot")
st.sidebar.success("✅ Online")

# --- 3. API Key Setup ---
# PASTE YOUR KEY HERE
raw_api_key = "AIzaSyAJLhXLQaY4U-u6ipI_IFROXi_n1m5MAug"

my_key = raw_api_key.strip()
os.environ["GOOGLE_API_KEY"] = my_key

# Navigation
page = st.sidebar.radio("Navigate", ["🤖 AI Tax Assistant", "🧮 Smart Tax Estimator", "📅 Compliance Calendar"])

# --- 4. Main Logic ---

# ==========================
# 🤖 TAB 1: AI ASSISTANT
# ==========================
if page == "🤖 AI Tax Assistant":
    st.title("🤖 AI Tax Assistant")
    st.markdown("Your **Real-time Compliance Copilot**. Ask about GST, 44ADA, or Penalties.")
    
    user_query = st.text_input("Describe your situation (e.g., 'I am a freelance designer earning 15L...'):")
    
    if st.button("Ask Copilot"):
        if "PASTE" in my_key:
             st.error("❌ Please paste your API Key in app.py line 25")
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
                    st.markdown(result)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================
# 🧮 TAB 2: SMART ESTIMATOR (Updated for ALL PS Users)
# ==========================
elif page == "🧮 Smart Tax Estimator":
    st.title("🧮 Smart Tax Estimator (FY 2025-26)")
    st.markdown("Calculate tax for **Micro-Businesses** & **Freelancers**.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Business Details")
        
        # NEW: Dropdown to select User Type (Crucial for PS compliance)
        user_type = st.selectbox(
            "I am a...", 
            ["Freelancer / Professional", "Small Trader / Shopkeeper"]
        )
        # SAVE TO SESSION STATE for Tab 3 to use
        st.session_state["user_type"] = user_type
        
        gross_income = st.number_input("Annual Revenue (₹)", min_value=0, step=50000, value=2000000)
        
        # DYNAMIC LOGIC SWITCH
        if user_type == "Freelancer / Professional":
            # Section 44ADA Logic (For Developers, Doctors, etc.)
            profit_rate = 0.50
            section_name = "Section 44ADA"
            desc = "As a professional, the govt assumes **50%** of your receipts are profit."
        else:
            # Section 44AD Logic (For Shopkeepers, Traders)
            # We assume digital payments (6%) for simplicity in hackathon
            profit_rate = 0.06 
            section_name = "Section 44AD"
            desc = "As a small trader (digital), the govt assumes only **6%** of your turnover is profit."

        st.info(f"💡 **{section_name} Logic:**\n{desc}")

    with col2:
        st.subheader("2. The Calculation")
        
        # 1. Regular Business (Comparison Baseline)
        # Traders usually have low margins (15%), Freelancers high (80%)
        if user_type == "Small Trader / Shopkeeper":
            normal_profit = gross_income * 0.15 
        else:
            normal_profit = gross_income * 0.80 
            
        # 2. Presumptive Profit (The "Hack")
        presumptive_profit = gross_income * profit_rate
        
        # Calculate Tax (Simplified New Regime Slabs FY 25-26)
        def calculate_tax(income):
            if income <= 300000: return 0
            tax = 0
            if income > 300000: tax += (min(income, 700000) - 300000) * 0.05
            if income > 700000: tax += (min(income, 1000000) - 700000) * 0.10
            if income > 1000000: tax += (min(income, 1200000) - 1000000) * 0.15
            if income > 1200000: tax += (min(income, 1500000) - 1200000) * 0.20
            if income > 1500000: tax += (income - 1500000) * 0.30
            
            # Rebate 87A (Tax free up to 7L)
            if income <= 700000: return 0
            
            return tax * 1.04 # Add 4% Cess

        tax_normal = calculate_tax(normal_profit)
        tax_presumptive = calculate_tax(presumptive_profit)
        
        savings = tax_normal - tax_presumptive

        # DISPLAY METRICS
        c1, c2, c3 = st.columns(3)
        c1.metric("Regular Tax", f"₹{tax_normal:,.0f}")
        c2.metric(f"{section_name} Tax", f"₹{tax_presumptive:,.0f}", delta=f"-₹{savings:,.0f}", delta_color="inverse")
        c3.metric("You Save", f"₹{savings:,.0f}")

        # VISUAL CHART
        chart_data = pd.DataFrame({
            "Regime": ["Regular Audit", f"Presumptive ({section_name})"],
            "Tax Payable": [tax_normal, tax_presumptive]
        })
        st.bar_chart(chart_data, x="Regime", y="Tax Payable", color="#00FF00")

# ==========================
# 📅 TAB 3: PROACTIVE CALENDAR (Smart & Interactive)
# ==========================
elif page == "📅 Compliance Calendar":
    st.title("📅 Proactive Compliance Calendar")
    st.markdown("### 🛡️ Your Shield Against Penalties")
    
    # 1. DEMO MODE: Time Travel Logic
    # Allows judges to see how the app reacts to different dates
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Hackathon Demo Controls")
    simulated_date = st.sidebar.date_input("🕒 Simulate Today's Date", date(2026, 3, 1))
    st.caption(f"Current Simulation: **{simulated_date.strftime('%d %b %Y')}**")

    # 2. Get User Context (From Tab 2 if available, else default)
    user_persona = st.session_state.get("user_type", "Freelancer / Professional")
    st.info(f"Viewing Timeline for: **{user_persona}** (Presumptive Scheme)")

    # 3. Smart Deadline Data (Specific to 44AD/ADA)
    # 44AD/ADA users only pay Advance Tax once (March 15), not quarterly!
    deadlines = [
        {
            "Event": "Advance Tax (100% Payment)", 
            "Date": date(2026, 3, 15), 
            "Type": "Money",
            "Why": "Presumptive users must pay 100% tax by Mar 15 to avoid 1% monthly interest.",
            "Penalty": "1% interest per month (Sec 234C)"
        },
        {
            "Event": "GST Return (QRMP Scheme)", 
            "Date": date(2026, 3, 31), 
            "Type": "Filing",
            "Why": "Quarterly return for small businesses.",
            "Penalty": "₹50/day late fee"
        },
        {
            "Event": "ITR Filing (Form ITR-4)", 
            "Date": date(2026, 7, 31), 
            "Type": "Filing",
            "Why": "The final deadline to declare your income.",
            "Penalty": "₹5,000 flat penalty"
        },
    ]

    # 4. Logic to Sort and Find Urgent
    upcoming_deadlines = [d for d in deadlines if d["Date"] >= simulated_date]
    past_deadlines = [d for d in deadlines if d["Date"] < simulated_date]
    
    upcoming_deadlines.sort(key=lambda x: x["Date"])

    # 5. DASHBOARD UI
    if upcoming_deadlines:
        next_event = upcoming_deadlines[0]
        days_left = (next_event["Date"] - simulated_date).days
        
        # Dynamic Alert Banner
        if days_left <= 7:
            alert_color = "error"
            msg_prefix = "🚨 CRITICAL ACTION REQUIRED:"
        elif days_left <= 30:
            alert_color = "warning"
            msg_prefix = "⚠️ Upcoming Deadline:"
        else:
            alert_color = "info"
            msg_prefix = "ℹ️ Next Compliance:"

        # The "Big Banner"
        if alert_color == "error":
            st.error(f"{msg_prefix} **{next_event['Event']}** is due in **{days_left} DAYS**!")
        elif alert_color == "warning":
            st.warning(f"{msg_prefix} **{next_event['Event']}** is due in **{days_left} DAYS**.")
        else:
            st.info(f"{msg_prefix} **{next_event['Event']}** is in **{days_left} days**.")

        # Action Buttons
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.write(f"**Consequence:** {next_event['Why']}")
        with c2:
            st.button(f"Pay Now ➝", key="pay_btn", help="Redirects to Income Tax Portal")
        with c3:
            st.button("🔔 Remind Me", key="remind_btn")
            
        st.progress(max(0, 100 - (days_left * 3)))
    else:
        st.success("🎉 You are completely compliant! No upcoming deadlines.")

    # 6. Detailed Timeline View
    st.markdown("### 🗓️ FY 2025-26 Compliance Roadmap")
    
    for item in deadlines:
        d_date = item["Date"]
        days_diff = (d_date - simulated_date).days
        
        # visual status
        if days_diff < 0:
            status_icon = "✅"
            status_text = "Completed / Overdue"
            row_color = "grey"
        elif days_diff <= 30:
            status_icon = "🔥" 
            status_text = f"Due in {days_diff} days"
            row_color = "red"
        else:
            status_icon = "📅"
            status_text = f"Due in {days_diff} days"
            row_color = "green"

        with st.expander(f"{status_icon} {d_date.strftime('%d %b %Y')} — {item['Event']}"):
            st.markdown(f"**Status:** {status_text}")
            st.markdown(f"**Why it matters:** {item['Why']}")
            st.error(f"⚠️ **Risk:** {item['Penalty']}")
            if days_diff >= 0:
                st.button(f"Prepare {item['Type']}", key=f"btn_{item['Event']}")

# Footer
st.markdown("---")
st.markdown("🏆 **Team Tech Titans**")