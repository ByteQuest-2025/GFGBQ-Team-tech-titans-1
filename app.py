import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go 
from datetime import datetime, date
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Page Config ---
st.set_page_config(
    page_title="TaxPilot", 
    page_icon="💰", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PREMIUM DARK MODE CSS ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* 1. Global Reset */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }

    /* 2. Backgrounds */
    .stApp {
        background-color: #050505; 
    }
    [data-testid="stSidebar"] {
        background-color: #0A0A0A;
        border-right: 1px solid #1F2937;
    }

    /* 3. HEADER FIX */
    header[data-testid="stHeader"] {
        background-color: #050505 !important;
    }
    header[data-testid="stHeader"] * {
        color: #E0E0E0 !important;
    }

    /* 4. Headers (Neon Glow) */
    h1, h2, h3 {
        color: #FFFFFF !important;
        text-shadow: 0 0 10px rgba(0, 200, 83, 0.4);
        font-weight: 800 !important;
    }

    /* 5. Metric Cards */
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
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }

    /* 6. Input Fields */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #161B22 !important; 
        color: #E0E0E0 !important;
        border: 1px solid #30363D;
    }
    
    /* 7. Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00C853, #009688) !important;
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Hide Defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar Navigation ---
st.sidebar.title("💰 TaxPilot")
st.sidebar.caption("AI Tax & Compliance for India")
st.sidebar.markdown("---")
st.sidebar.success("✅ System Online")

# --- 4. API Key Setup ---
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
    st.markdown("---")
    
    user_query = st.text_input("Describe your situation (e.g., 'I am a freelance designer earning 15L...'):")
    
    if st.button("🚀 Ask Copilot"):
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
                    st.markdown(f"""
                    <div style="background-color: #111827; padding: 20px; border-radius: 10px; border-left: 5px solid #00C853; color: #E0E0E0;">
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
    st.markdown("---")

    col1, col2 = st.columns([1, 1], gap="large")

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

        st.markdown(f"""
        <div style="background-color: #064E3B; padding: 15px; border-radius: 8px; border: 1px solid #059669; color: #A7F3D0; margin-top: 10px;">
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

        st.markdown("<br>", unsafe_allow_html=True)

        # --- DETAILED PLOTLY CHART (Upgraded) ---
        fig = go.Figure()

        # 1. Regular Audit Bar (Dark Grey)
        fig.add_trace(go.Bar(
            x=['Regular Audit'],
            y=[tax_normal],
            name='Regular Tax',
            marker=dict(color='#374151', line=dict(color='#6B7280', width=1)),
            text=[f"₹{tax_normal:,.0f}"],
            textposition='auto',
            textfont=dict(color='white', size=16, family="Inter", weight="bold"),
            hoverinfo='y+name'
        ))

        # 2. Presumptive Tax Bar (Neon Green)
        fig.add_trace(go.Bar(
            x=[f'Presumptive ({section_name})'],
            y=[tax_presumptive],
            name=f'{section_name} Tax',
            marker=dict(color='#00C853', line=dict(color='#69F0AE', width=2)),
            text=[f"₹{tax_presumptive:,.0f}"],
            textposition='auto',
            textfont=dict(color='black', size=16, family="Inter", weight="bold"),
            hoverinfo='y+name'
        ))

        # 3. Add Annotation (Arrow showing Savings)
        if savings > 0:
            fig.add_annotation(
                x=f'Presumptive ({section_name})',
                y=tax_presumptive + (savings / 2),
                text=f"<b>You Save ₹{savings:,.0f}!</b>",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#00E676",
                ax=0,
                ay=-40,
                font=dict(color="#00E676", size=14)
            )

        # 4. Final Layout
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(color='#E0E0E0', size=14, family="Inter")
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333333',
                gridwidth=1,
                tickfont=dict(color='#E0E0E0', size=12, family="Inter"),
                tickformat="₹",
                zeroline=False
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================
# 📅 TAB 3: PROACTIVE CALENDAR
# ==========================
elif page == "📅 Compliance Calendar":
    st.title("📅 Proactive Compliance Calendar")
    st.markdown("### 🛡️ Your Shield Against Penalties")
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Hackathon Demo Controls")
    simulated_date = st.sidebar.date_input("🕒 Simulate Today's Date", date(2026, 3, 1))
    
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
            bg, border, txt, icon = "#450a0a", "#ef4444", "#fecaca", "🚨"
        elif days_left <= 30:
            bg, border, txt, icon = "#422006", "#eab308", "#fef08a", "⚠️"
        else:
            bg, border, txt, icon = "#064e3b", "#10b981", "#a7f3d0", "ℹ️"

        st.markdown(f"""
        <div style="padding: 20px; border-radius: 8px; background-color: {bg}; border: 1px solid {border}; color: {txt}; margin-bottom: 25px;">
            <h3 style="margin:0; color: {txt} !important;">{icon} {next_event['Event']}</h3>
            <p style="margin:5px 0 0 0; color: {txt} !important;">Due in <strong>{days_left} DAYS</strong>. {next_event['Why']}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: st.button(f"Pay Now ➝", key="pay_btn")
        with c2: st.button("🔔 Remind Me", key="remind_btn")
            
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
st.markdown("🏆 **Team Tech Titans** | Built for Hackathon 2026")