import streamlit as st
import os
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Page Config ---
st.set_page_config(page_title="TaxPilot", page_icon="💰", layout="wide")

# --- 2. Sidebar Navigation ---
st.sidebar.title("💰 TaxPilot")
st.sidebar.markdown("Compliance Copilot for Gig Workers")

# --- 3. API Key Setup (The Fix) ---
# PASTE YOUR KEY INSIDE THE QUOTES BELOW. 
# Make sure there are NO spaces before or after the key.
raw_api_key = "my_key"

# This line removes any accidental spaces you might have copied
my_key = raw_api_key.strip()

# Force the key into the environment
os.environ["GOOGLE_API_KEY"] = my_key

# Debugging: Show us if the key is loaded (Prints to sidebar)
if my_key == "PASTE_YOUR_KEY_HERE":
    st.sidebar.error("❌ You forgot to paste your key in the code!")
elif len(my_key) < 30:
    st.sidebar.error("❌ Key looks too short. Please copy it again.")
else:
    st.sidebar.success(f"✅ Key Loaded! (Starts with {my_key[:4]}...)")

page = st.sidebar.radio("Navigate", ["🤖 AI Tax Assistant", "🧮 Tax Estimator", "📅 Compliance Calendar"])

# --- 4. Main Page Logic ---
if page == "🤖 AI Tax Assistant":
    st.title("🤖 AI Tax Assistant")
    st.markdown("Ask me anything about Indian Tax Rules for Freelancers (Presumptive Taxation, GST, etc.)")
    
    user_query = st.text_input("Enter your tax question:")
    
    if st.button("Ask AI"):
        if not user_query:
            st.warning("Please enter a question first!")
        elif my_key == "PASTE_YOUR_KEY_HERE":
             st.error("Please open app.py and paste your API Key in line 16.")
        else:
            with st.spinner("Consulting the Tax Expert (Gemini 2.5)..."):
                try:
                    # We use Gemini 2.5 Flash (Standard for 2026)
                    # If this fails, try "gemini-2.0-flash-exp"
                    gemini_llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        verbose=True,
                        temperature=0.5,
                        google_api_key=my_key
                    )

                    tax_expert = Agent(
                        role='Senior Indian Tax Advisor',
                        goal='Provide accurate, legal tax advice for Indian freelancers.',
                        backstory="You are a Chartered Accountant (CA) in India with 20 years of experience.",
                        verbose=True,
                        allow_delegation=False,
                        llm=gemini_llm 
                    )

                    answer_task = Task(
                        description=f"Analyze this query: '{user_query}'. Answer based on FY 2025-26 rules.",
                        expected_output="A clear text response.",
                        agent=tax_expert
                    )

                    crew = Crew(
                        agents=[tax_expert],
                        tasks=[answer_task],
                        verbose=True,
                        memory=False 
                    )
                    
                    result = crew.kickoff()
                    
                    st.success("Analysis Complete!")
                    st.markdown("### 💡 AI Response:")
                    st.markdown(result)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    # If 404 happens again, it means we need to try the 2.0 model
                    if "404" in str(e):
                        st.info("💡 Try changing 'gemini-2.5-flash' to 'gemini-2.0-flash-exp' in the code.")

elif page == "🧮 Tax Estimator":
    st.title("🧮 Simple Tax Estimator")
    st.write("Calculators coming soon.")

elif page == "📅 Compliance Calendar":
    st.title("📅 Compliance Calendar")
    st.write("Deadlines coming soon.")