# med_tracker.py - Complete Agentic AI Medication Tracker
import streamlit as st
import sqlite3
import requests
from datetime import datetime
from med_agent import TrueMedicationAgent

# Page setup
st.set_page_config(page_title="Agentic Med Tracker", layout="centered")
st.title("🧠 Agentic AI Medication Tracker")

# Initialize database
def init_db():
    conn = sqlite3.connect('meds.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS dose_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medication_id) REFERENCES medications (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Initialize AI Agent (lazy load to avoid API key issues)
@st.cache_resource
def get_agent():
    try:
        return TrueMedicationAgent()
    except Exception as e:
        st.warning(f"AI Agent initialization warning: {e}")
        # Return agent without OpenAI key (will use fallbacks)
        return TrueMedicationAgent(openai_key="")

agent = get_agent()

# --- TABBED INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🤖 AI Agent", "💊 Medications", "🔧 MCP Tools"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("📊 Dashboard")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM medications")
        med_count = c.fetchone()[0]
        conn.close()
        st.metric("Active Medications", med_count)
    
    with col2:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dose_logs WHERE DATE(taken_at) = DATE('now')")
        today_doses = c.fetchone()[0]
        conn.close()
        st.metric("Doses Today", today_doses)
    
    with col3:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM medications WHERE id NOT IN (SELECT medication_id FROM dose_logs WHERE DATE(taken_at) = DATE('now'))")
        missed = c.fetchone()[0]
        conn.close()
        st.metric("Missed Today", missed)
    
    # Today's schedule
    st.subheader("📅 Today's Schedule")
    conn = sqlite3.connect('meds.db')
    c = conn.cursor()
    c.execute("SELECT name, dosage, frequency FROM medications")
    meds = c.fetchall()
    conn.close()
    
    if meds:
        for name, dosage, freq in meds:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{name}**")
                if dosage:
                    st.caption(f"Dosage: {dosage}")
            with col2:
                if freq:
                    st.write(freq)
            with col3:
                if st.button("✅ Taken", key=f"dash_taken_{name}"):
                    conn = sqlite3.connect('meds.db')
                    c = conn.cursor()
                    c.execute("SELECT id FROM medications WHERE name = ?", (name,))
                    med_id = c.fetchone()[0]
                    c.execute("INSERT INTO dose_logs (medication_id) VALUES (?)", (med_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Logged {name}!")
                    st.rerun()
    else:
        st.info("No medications scheduled. Add some in the Medications tab!")
    
    # Recent activity
    st.subheader("📝 Recent Activity")
    conn = sqlite3.connect('meds.db')
    c = conn.cursor()
    c.execute('''
        SELECT m.name, l.taken_at 
        FROM dose_logs l
        JOIN medications m ON l.medication_id = m.id
        ORDER BY l.taken_at DESC
        LIMIT 5
    ''')
    recent = c.fetchall()
    conn.close()
    
    if recent:
        for name, taken_at in recent:
            st.write(f"• **{name}** at {taken_at}")
    else:
        st.info("No recent doses logged")

# --- TAB 2: AI AGENT ---
with tab2:
    st.header("🤖 AI Health Agent")
    
    ai_tab1, ai_tab2, ai_tab3 = st.tabs(["Symptom Analysis", "Health Planning", "Agent Context"])
    
    with ai_tab1:
        st.subheader("AI Symptom Analysis")
        symptoms = st.text_area("Describe your symptoms:")
        
        if symptoms and st.button("Analyze with AI"):
            with st.spinner("AI agent analyzing..."):
                conn = sqlite3.connect('meds.db')
                c = conn.cursor()
                c.execute("SELECT name FROM medications")
                user_meds = [row[0] for row in c.fetchall()]
                conn.close()
                
                result = agent.analyze_symptoms(symptoms, user_meds)
                
                if isinstance(result, dict) and "ai_analysis" in result:
                    st.success("AI Analysis Complete")
                    st.markdown(result["ai_analysis"])
                    
                    if "fda_recommendations" in result and result["fda_recommendations"]:
                        st.write("**FDA Recommendations:**")
                        recs = result["fda_recommendations"]
                        if isinstance(recs, list) and len(recs) > 0:
                            if isinstance(recs[0], dict):
                                for med in recs[:3]:
                                    st.write(f"• **{med['name']}**")
                                    if med.get('purpose'):
                                        st.caption(med['purpose'][:100] + "...")
                            else:
                                for med in recs[:3]:
                                    st.write(f"• {med}")
                else:
                    st.info("Using basic symptom matching (AI not available)")
                    st.write(result)
    
    with ai_tab2:
        st.subheader("AI Health Planning")
        goal = st.text_input("Your health goal:")
        
        if goal and st.button("Create AI Plan"):
            user_id = "current_user"
            conn = sqlite3.connect('meds.db')
            c = conn.cursor()
            c.execute("SELECT name FROM medications")
            user_meds = ", ".join([row[0] for row in c.fetchall()])
            conn.close()
            
            plan = agent.create_health_plan(user_id, goal, user_meds)
            
            st.success(f"Plan: {plan['goal']}")
            st.write(f"Progress: {plan['progress']}%")
            
            for i, step in enumerate(plan["steps"], 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i}. {step}")
                with col2:
                    if st.button("✅", key=f"plan_{i}"):
                        agent.planner.update_progress(plan["id"], step)
                        st.success("Updated!")
                        st.rerun()
    
    with ai_tab3:
        st.subheader("Agent with MCP Context")
        query = st.text_input("Ask agent (uses your data):")
        
        if query and st.button("Ask with Context"):
            with st.spinner("Agent gathering context..."):
                result = agent.analyze_with_context(query)
                
                st.success(f"Used {len(result['tools_used'])} tools")
                
                with st.expander("See gathered context"):
                    for tool, content in result.get("context_gathered", {}).items():
                        st.write(f"**{tool}:**")
                        st.text(str(content)[:200] + "..." if len(str(content)) > 200 else str(content))
                
                st.write("**AI Analysis:**")
                st.info(result.get("ai_analysis", "No analysis available"))

# --- TAB 3: MEDICATIONS ---
with tab3:
    st.header("💊 Medication Management")
    
    # Add medication
    st.subheader("Add Medication")
    with st.form("add_med_form"):
        name = st.text_input("Name")
        dosage = st.text_input("Dosage")
        frequency = st.text_input("Frequency")
        
        if st.form_submit_button("Add"):
            if name:
                conn = sqlite3.connect('meds.db')
                c = conn.cursor()
                c.execute(
                    "INSERT INTO medications (name, dosage, frequency) VALUES (?, ?, ?)",
                    (name, dosage, frequency)
                )
                conn.commit()
                conn.close()
                st.success(f"Added {name}!")
                st.rerun()
    
    # List medications
    st.subheader("Your Medications")
    conn = sqlite3.connect('meds.db')
    c = conn.cursor()
    c.execute("SELECT * FROM medications ORDER BY created_at DESC")
    meds = c.fetchall()
    conn.close()
    
    if meds:
        for med in meds:
            med_id, name, dosage, freq, created = med
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{name}**")
                if dosage:
                    st.caption(f"Dosage: {dosage}")
                if freq:
                    st.caption(f"Frequency: {freq}")
            with col2:
                if st.button("✅ Taken", key=f"med_taken_{med_id}"):
                    conn = sqlite3.connect('meds.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO dose_logs (medication_id) VALUES (?)", (med_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Logged {name}!")
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{med_id}"):
                    conn = sqlite3.connect('meds.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM medications WHERE id = ?", (med_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Deleted {name}")
                    st.rerun()
    else:
        st.info("No medications yet")

# --- TAB 4: MCP TOOLS ---
with tab4:
    st.header("🔧 MCP Tools")
    
    st.write("""
    **Connected to your MCP file server!**
    The AI agent can access your files and data through these tools.
    """)
    
    # Quick tools
    tool_choice = st.selectbox(
        "Select tool:",
        ["Check Schedule", "View Logs", "List Files", "Export Report"]
    )
    
    if tool_choice == "Check Schedule":
        if st.button("Run Check Schedule"):
            try:
                result = agent.mcp_client.call_tool("check_medication_schedule")
                st.text_area("Schedule:", result, height=200)
            except:
                st.warning("MCP server might be offline. Using local data...")
                conn = sqlite3.connect('meds.db')
                c = conn.cursor()
                c.execute("SELECT name, dosage, frequency FROM medications")
                meds = c.fetchall()
                conn.close()
                result = "\n".join([f"{name}: {dosage} - {freq}" for name, dosage, freq in meds])
                st.text_area("Schedule:", result or "No medications", height=200)
    
    elif tool_choice == "View Logs":
        days = st.slider("Days:", 1, 30, 7)
        if st.button("Get Logs"):
            try:
                result = agent.mcp_client.call_tool("get_medication_logs", days=days)
                st.text_area(f"Last {days} days:", result, height=300)
            except:
                st.warning("Using local data...")
                conn = sqlite3.connect('meds.db')
                c = conn.cursor()
                cutoff = (datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
                c.execute('''
                    SELECT m.name, l.taken_at 
                    FROM dose_logs l
                    JOIN medications m ON l.medication_id = m.id
                    WHERE DATE(l.taken_at) >= DATE(?)
                    ORDER BY l.taken_at DESC
                ''', (cutoff,))
                logs = c.fetchall()
                conn.close()
                result = "\n".join([f"{name} at {time}" for name, time in logs]) if logs else f"No logs in {days} days"
                st.text_area(f"Last {days} days:", result, height=300)
    
    elif tool_choice == "List Files":
        directory = st.text_input("Directory:", ".")
        if st.button("List"):
            try:
                result = agent.mcp_client.call_tool("list_files", directory=directory)
                st.text_area("Files:", str(result), height=300)
            except:
                import os
                result = str(os.listdir(directory)) if os.path.exists(directory) else "Directory not found"
                st.text_area("Files:", result, height=300)
    
    elif tool_choice == "Export Report":
        if st.button("Export"):
            try:
                result = agent.mcp_client.call_tool("export_health_report", directory=".")
                st.success("Report exported!")
                st.code(result)
            except Exception as e:
                st.error(f"Export failed: {e}")

# --- FOOTER ---
st.divider()
st.caption("⚠️ **Disclaimer:** This is for informational purposes only. Always consult healthcare professionals.")
st.caption("🔗 **Powered by:** Streamlit + SQLite + MCP + AI Agent")

# Auto-refresh every 60 seconds
if st.button("🔄 Refresh"):
    st.rerun()

