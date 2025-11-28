# med_tracker.py
import streamlit as st
import sqlite3
import requests
from datetime import datetime

# Page setup
st.set_page_config(page_title="Simple Med Tracker", layout="centered")
st.title("💊 Simple Medication Tracker")

# Database setup
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
st.success("✅ Database ready!")

# Enhanced Add medication section with API lookup
st.header("➕ Add Medication")

# API lookup section
st.subheader("🔍 Look up Medication Info")
drug_search = st.text_input("Search FDA database for medication name")

if drug_search and st.button("Search FDA Database"):
    with st.spinner("Searching FDA database..."):
        try:
            # OpenFDA API call - FREE, no API key needed
            response = requests.get(
                f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_search}&limit=1"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    drug_info = data['results'][0]
                    brand_name = drug_info['openfda'].get('brand_name', ['Unknown'])[0]
                    generic_name = drug_info['openfda'].get('generic_name', ['Unknown'])[0]
                    
                    st.success(f"Found: {brand_name}")
                    st.write(f"**Generic Name:** {generic_name}")
                    
                    # Pre-fill the form with found data
                    st.session_state.pre_fill_name = brand_name
                    st.session_state.pre_fill_dosage = "Check label for dosage"
                else:
                    st.warning("No medication found with that name")
            else:
                st.error("FDA API unavailable - try manual entry")
                
        except Exception as e:
            st.error(f"API error: {str(e)}")

# Manual entry form
st.subheader("📝 Manual Entry")
with st.form("add_med_form"):
    # Use pre-filled data if available from API search
    default_name = st.session_state.get('pre_fill_name', '')
    default_dosage = st.session_state.get('pre_fill_dosage', '')
    
    name = st.text_input("Medication Name", value=default_name)
    dosage = st.text_input("Dosage (e.g., 500mg)", value=default_dosage)
    frequency = st.text_input("Frequency (e.g., Twice daily)")
    
    if st.form_submit_button("Add Medication"):
        if name:
            conn = sqlite3.connect('meds.db')
            c = conn.cursor()
            c.execute(
                "INSERT INTO medications (name, dosage, frequency) VALUES (?, ?, ?)",
                (name, dosage, frequency)
            )
            conn.commit()
            conn.close()
            
            # Clear pre-fill after successful add
            if 'pre_fill_name' in st.session_state:
                del st.session_state.pre_fill_name
            if 'pre_fill_dosage' in st.session_state:
                del st.session_state.pre_fill_dosage
                
            st.success(f"✅ Added {name}!")
            st.rerun()
        else:
            st.warning("Please enter at least a medication name")
# Dose history section
st.header("📊 Dose History")

conn = sqlite3.connect('meds.db')
c = conn.cursor()
c.execute('''
    SELECT m.name, m.dosage, l.taken_at 
    FROM dose_logs l
    JOIN medications m ON l.medication_id = m.id
    ORDER BY l.taken_at DESC
    LIMIT 10
''')
recent_doses = c.fetchall()
conn.close()

if recent_doses:
    for dose in recent_doses:
        name, dosage, taken_at = dose
        st.write(f"**{name}** - {dosage} - {taken_at}")
else:
    st.info("No doses logged yet. Take your meds! 💊")
