# med_tracker.py - Clean AI Medication Tracker
import streamlit as st
import sqlite3
import requests
from datetime import datetime
from med_agent import TrueMedicationAgent
from symptom_db import get_medications_for_symptoms

# HIDE STREAMLIT DEPLOY BUTTON
hide_deploy_button = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_deploy_button, unsafe_allow_html=True)

# Page setup
st.set_page_config(page_title="Agentic Med Tracker", layout="centered")
st.title("🧠 Agentic AI Medication Tracker")


# Initialize database
def init_db():
    conn = sqlite3.connect("meds.db")
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dose_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medication_id) REFERENCES medications (id)
        )
    """
    )

    conn.commit()
    conn.close()


# Initialize database
init_db()


# Initialize AI Agent
# Initialize AI Agent
@st.cache_resource
def get_agent():

    # ONLY use st.secrets - nothing else
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = None

    return TrueMedicationAgent(openai_key=api_key)


agent = get_agent()

# --- TABBED INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Dashboard", "🤖 Check Symptoms", "💊 Medications", "🔌 Status"]
)

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("📊 Dashboard")

    # Quick stats
    col1, col2, col3 = st.columns(3)

    with col1:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM medications")
        med_count = c.fetchone()[0]
        conn.close()
        st.metric("Active Medications", med_count)

    with col2:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dose_logs WHERE DATE(taken_at) = DATE('now')")
        today_doses = c.fetchone()[0]
        conn.close()
        st.metric("Doses Today", today_doses)

    with col3:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM medications WHERE id NOT IN (SELECT medication_id FROM dose_logs WHERE DATE(taken_at) = DATE('now'))"
        )
        missed = c.fetchone()[0]
        conn.close()
        st.metric("Missed Today", missed)

    # Today's schedule
    st.subheader("📅 Today's Schedule")
    conn = sqlite3.connect("meds.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, name, dosage, frequency FROM medications"
    )  # CHANGED: Added id
    meds = c.fetchall()
    conn.close()

    if meds:
        for med_id, name, dosage, freq in meds:  # CHANGED: Unpack med_id
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{name}**")
                if dosage:
                    st.caption(f"Dosage: {dosage}")
            with col2:
                if freq:
                    st.write(freq)
            with col3:
                # CHANGED: Key uses med_id instead of name
                if st.button("✅ Taken", key=f"dash_taken_{med_id}"):
                    conn = sqlite3.connect("meds.db")
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO dose_logs (medication_id) VALUES (?)", (med_id,)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Logged {name}!")
                    st.rerun()
    else:
        st.info("No medications scheduled. Add some in the Medications tab!")

    # Recent activity
    st.subheader("📝 Recent Activity")
    conn = sqlite3.connect("meds.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT m.name, l.taken_at 
        FROM dose_logs l
        JOIN medications m ON l.medication_id = m.id
        ORDER BY l.taken_at DESC
        LIMIT 5
    """
    )
    recent = c.fetchall()
    conn.close()

    if recent:
        for name, taken_at in recent:
            st.write(f"• **{name}** at {taken_at}")
    else:
        st.info("No recent doses logged")

# --- TAB 2: SYMPTOM CHECKER ---
with tab2:
    st.header("🤖 AI Symptom Checker")

    st.write(
        """
    Describe your symptoms and get:
    - FDA-approved medication suggestions
    - AI medical advice
    - Information about your current medications
    """
    )

    # User input
    symptoms = st.text_area(
        "Describe your symptoms:",
        placeholder="Example: headache and fever, sore throat, chest pain...",
        key="symptoms_input",
        height=100,
    )

    # Clean button layout - ONLY TWO BUTTONS
    col1, col2 = st.columns([4, 1])

    with col1:
        analyze_clicked = st.button(
            "🔍 Check Symptoms with AI & FDA",
            type="primary",
            use_container_width=True,
            key="check_symptoms_btn",
        )

    with col2:
        if st.button("🔄 Clear Results", use_container_width=True, key="clear_btn"):
            # Clear results only
            st.session_state.last_results = None
            st.session_state.last_symptoms = ""
            st.session_state.last_user_meds = []
            st.rerun()

    # Example symptoms hint
    st.caption("💡 **Try:** headache, fever, cough, sore throat, nausea, fatigue")

    # Process symptom analysis when button is clicked
    if analyze_clicked and symptoms:
        with st.spinner("🔍 Analyzing symptoms..."):
            # Get user's current medications for context
            conn = sqlite3.connect("meds.db")
            c = conn.cursor()
            c.execute("SELECT name FROM medications")
            user_meds = [row[0] for row in c.fetchall()]
            conn.close()

            try:
                # 1. Get FDA medications (this is the working function)
                fda_medications = get_medications_for_symptoms(symptoms)

                # 2. Get AI analysis (now actually used!)
                try:
                    ai_analysis = agent.analyze_symptoms(symptoms, user_meds)

                    # Check if we got real AI results
                    if (
                        ai_analysis
                        and isinstance(ai_analysis, dict)
                        and "ai_analysis" in ai_analysis
                    ):
                        ai_text = ai_analysis["ai_analysis"]
                    else:
                        ai_text = (
                            "AI analysis completed. Review FDA recommendations above."
                        )

                except Exception as ai_error:
                    ai_text = "AI insights available. Review FDA medications above and consider consulting a healthcare provider for personalized advice."

                # 3. Combine results
                result = {
                    "fda_recommendations": fda_medications,
                    "ai_analysis": ai_text,
                    "user_medications": user_meds,
                }

                st.session_state.last_results = result
                st.session_state.last_symptoms = symptoms
                st.session_state.last_user_meds = user_meds

            except Exception as e:
                st.error(f"Error getting medications: {str(e)}")
                result = None

    # Display results if we have them
    if "last_results" in st.session_state and st.session_state.last_results:
        result = st.session_state.last_results
        symptoms = st.session_state.get("last_symptoms", "")
        user_meds = st.session_state.get("last_user_meds", [])

        st.success(f"✅ Analysis complete for: '{symptoms}'")

        # Display FDA recommendations
        if isinstance(result, dict) and "fda_recommendations" in result:
            fda_results = result["fda_recommendations"]

            if fda_results and isinstance(fda_results, list) and len(fda_results) > 0:
                st.subheader(f"💊 FDA-Approved Medications ({len(fda_results)} found)")

                # Check what type of results we have
                if isinstance(fda_results[0], dict):
                    # Structured results with details
                    for i, med in enumerate(fda_results[:12]):
                        with st.container():
                            st.markdown(f"**{i+1}. {med.get('name', 'Medication')}**")

                            if med.get("condition"):
                                st.caption(f"🩺 For: {med['condition']}")

                                # Simple AI context notes
                                condition_notes = {
                                    "diabetes": "💡 **AI Note:** Monitor blood glucose levels regularly",
                                    "hyperglycemia": "💡 **AI Note:** High blood sugar requires medical attention",
                                    "dehydration": "💡 **AI Note:** Ensure adequate fluid intake",
                                    "injury": "💡 **AI Note:** Rest injured area, watch for infection signs",
                                    "liver disease": "💡 **AI Note:** Requires specialist consultation",
                                    "pain": "💡 **AI Note:** Use as directed, don't exceed dosage",
                                }

                                condition_lower = med["condition"].lower()
                                for key, note in condition_notes.items():
                                    if key in condition_lower:
                                        st.info(note)
                                        break

                            if med.get("purpose"):
                                purpose = med["purpose"]
                                if len(purpose) > 300:
                                    purpose = purpose[:297] + "..."
                                st.write(purpose)

                            if med.get("source"):
                                st.caption(f"📋 Source: {med['source']}")

                            # Add to My Meds button
                            col1, col2 = st.columns([4, 1])
                            with col2:
                                if st.button("➕ Add to My Meds", key=f"add_{i}"):
                                    # Actually add to database
                                    conn = sqlite3.connect("meds.db")
                                    c = conn.cursor()
                                    c.execute(
                                        "INSERT INTO medications (name, dosage, frequency) VALUES (?, ?, ?)",
                                        (
                                            med.get("name", ""),
                                            "As directed",
                                            f"For {med.get('condition', 'general use')}",
                                        ),
                                    )
                                    conn.commit()
                                    conn.close()

                                    st.success(
                                        f"✅ Added {med.get('name', 'medication')}!"
                                    )
                                    st.rerun()

                            st.divider()
                else:
                    # Simple list results
                    st.write("Consider these medications:")
                    for med in fda_results[:12]:
                        st.write(f"• {med}")
            else:
                st.info("No specific FDA recommendations found for these symptoms.")

        # Display AI analysis
        st.subheader("🧠 AI-Powered Insights")

        if isinstance(result, dict) and "ai_analysis" in result:
            ai_advice = result["ai_analysis"]

            if (
                ai_advice
                and "AI analysis unavailable" not in ai_advice
                and "AI insights available" not in ai_advice
            ):
                # Show AI insights in scrollable area
                with st.expander("🔍 View Detailed AI Analysis", expanded=True):
                    st.text_area(
                        "Full AI Analysis",
                        value=ai_advice,
                        height=300,
                        disabled=True,
                        key=f"ai_full_{hash(ai_advice[:50])}",
                    )

                # Also show a summary preview
                st.markdown("### 📋 AI Summary")

                # Extract first few lines for preview
                lines = ai_advice.split("\n")
                preview_lines = []
                for line in lines[:6]:
                    if line.strip():
                        preview_lines.append(line)

                for line in preview_lines:
                    st.markdown(line)

            else:
                # Fallback
                st.info(
                    """
                **General Health Guidance:**
                - Rest and maintain hydration
                - Monitor symptoms closely
                - Follow medication directions
                - Contact doctor if concerns arise
                
                *For personalized AI analysis, ensure OpenAI API key is configured in my_secrets.py*
                """
                )
        else:
            st.info(
                """
            **General Recommendations:**
            1. Consider over-the-counter medications based on symptoms
            2. Rest and maintain proper hydration
            3. Consult healthcare professional if symptoms persist
            4. Keep track of symptom patterns
            """
            )

        # Show user's current medications
        if user_meds:
            st.subheader("📋 Your Current Medications")
            st.write(", ".join(user_meds) if user_meds else "No medications")

            if len(user_meds) > 1:
                st.warning(
                    "⚠️ **Important:** Always consult your doctor or pharmacist about potential medication interactions."
                )

        # Disclaimer
        st.info(
            """
        ⚠️ **Disclaimer:** This information is for educational purposes only. 
        Always consult a healthcare professional for medical advice, diagnosis, or treatment.
        """
        )

# --- TAB 3: MEDICATIONS ---
with tab3:
    st.header("💊 Medication Management")

    # Auto-fill from AI suggestions
    auto_fill = st.session_state.get("auto_fill_med", "")

    # Add medication
    st.subheader("Add Medication")
    with st.form("add_med_form"):
        name = st.text_input("Medication Name", value=auto_fill)
        dosage = st.text_input("Dosage (e.g., 500mg, 1 tablet)")
        frequency = st.text_input("Frequency (e.g., Twice daily, Every 6 hours)")

        submitted = st.form_submit_button("➕ Add Medication")

        if submitted:
            if name:
                conn = sqlite3.connect("meds.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO medications (name, dosage, frequency) VALUES (?, ?, ?)",
                    (name, dosage, frequency),
                )
                conn.commit()
                conn.close()

                # Clear auto-fill
                if "auto_fill_med" in st.session_state:
                    del st.session_state.auto_fill_med

                st.success(f"✅ Added {name} to your medications!")
                st.rerun()
            else:
                st.warning("Please enter at least a medication name")

    # List medications
    st.subheader("Your Medications")
    conn = sqlite3.connect("meds.db")
    c = conn.cursor()
    c.execute("SELECT * FROM medications ORDER BY created_at DESC")
    meds = c.fetchall()
    conn.close()

    if meds:
        for med in meds:
            med_id, name, dosage, freq, created = med

            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.write(f"**{name}**")
                    if dosage:
                        st.caption(f"**Dosage:** {dosage}")
                    if freq:
                        st.caption(f"**Frequency:** {freq}")
                    st.caption(f"Added: {created}")

                with col2:
                    if st.button("✅ Taken Today", key=f"med_taken_{med_id}"):
                        conn = sqlite3.connect("meds.db")
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO dose_logs (medication_id) VALUES (?)",
                            (med_id,),
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Logged dose for {name}!")
                        st.rerun()

                with col3:
                    if st.button("🗑️", key=f"delete_{med_id}"):
                        conn = sqlite3.connect("meds.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM medications WHERE id = ?", (med_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted {name}")
                        st.rerun()

                st.divider()
    else:
        st.info("No medications yet. Add your first medication above!")

# --- TAB 4: STATUS ---
with tab4:
    # AI Status - ONLY checks st.secrets
    st.subheader("🧠 AI Status")

    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        if api_key and api_key.startswith("sk-"):
            st.success("✅ OpenAI Connected via Streamlit Secrets")
            st.caption("AI analysis enabled")
        else:
            st.warning("⚠️ Invalid OpenAI Key in Streamlit Secrets")
            st.caption("Key should start with 'sk-'")
    else:
        st.warning("⚠️ OpenAI Not Configured")
        st.caption("Add OPENAI_API_KEY to Streamlit Cloud Secrets")

    # FDA API Status
    st.subheader("💊 FDA API Status")
    try:
        test_response = requests.get(
            "https://api.fda.gov/drug/label.json?limit=1", timeout=3
        )
        if test_response.status_code == 200:
            st.success("✅ FDA API Connected")
            st.caption("Medication search active")
        else:
            st.warning(f"⚠️ FDA API Issue: Status {test_response.status_code}")
    except Exception as e:
        st.error(f"❌ FDA API Error: {str(e)[:50]}...")
        st.caption("Check internet connection")

    # Database Status
    st.subheader("💾 Database Status")
    try:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM medications")
        med_count = c.fetchone()[0]
        conn.close()
        st.success(f"✅ Database Connected ({med_count} medications)")
        st.caption("meds.db active")
    except Exception as e:
        st.error(f"❌ Database Error: {str(e)[:50]}...")

    # MCP Server Status (if exists)
    st.subheader("🔧 MCP Server")
    try:
        if hasattr(agent, "mcp_client") and agent.mcp_client.connected:
            st.success("✅ MCP Server Connected")
            st.caption("File tools available")
        else:
            st.info("ℹ️ MCP Server Not Detected")
            st.caption("Optional for file operations")
    except:
        st.info("ℹ️ MCP Not Configured")
        st.caption("Optional component")

    # Quick Stats
    st.subheader("📊 Quick Stats")
    col1, col2 = st.columns(2)

    with col1:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dose_logs WHERE DATE(taken_at) = DATE('now')")
        today_doses = c.fetchone()[0]
        conn.close()
        st.metric("Doses Today", today_doses)

    with col2:
        conn = sqlite3.connect("meds.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT DATE(taken_at)) FROM dose_logs")
        active_days = c.fetchone()[0]
        conn.close()
        st.metric("Tracking Days", active_days)

    # Health Tips
    st.subheader("💡 Tips")
    st.info(
        """
    • Check symptoms in Tab 2 for AI + FDA analysis
    • Add medications in Tab 3 for tracking
    • Log doses daily for best insights
    • Export data before major updates
    """
    )

# --- FOOTER & DISCLAIMERS ---
st.divider()

col1, col2 = st.columns([3, 1])

with col1:
    st.caption(
        """
    ⚠️ **Disclaimer:** This application provides health information for educational purposes only. 
    It is not a substitute for professional medical advice, diagnosis, or treatment. 
    Always seek the advice of your physician or other qualified health provider with any questions you may have.
    """
    )

with col2:
    if st.button("🔄 Refresh App"):
        st.rerun()

# Session state initialization
if "symptoms_input" not in st.session_state:
    st.session_state.symptoms_input = ""
if "auto_fill_med" not in st.session_state:
    st.session_state.auto_fill_med = ""
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_symptoms" not in st.session_state:
    st.session_state.last_symptoms = ""
if "last_user_meds" not in st.session_state:
    st.session_state.last_user_meds = []
