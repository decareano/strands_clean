import base64
import os
import logging
import json
import sqlite3
import datetime
from fastmcp.server import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("file_mcp_server")

# Initialize FastMCP server
mcp = FastMCP("file_mcp_server")

# --- YOUR ORIGINAL TOOLS ---
@mcp.tool()
def list_files(directory: str = ".") -> str:
    """Lists all files and directories within a specified directory."""
    try:
        files = os.listdir(directory)
        return f"Files in {directory}:\n" + "\n".join(files)
    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."

@mcp.tool()
def read_file(filepath: str) -> str:
    """Reads the content of a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return f"Content of {filepath}:\n\n{content}"
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except Exception as e:
        return f"Error reading file '{filepath}': {e}"

@mcp.tool()
def analyze_image(filepath: str) -> str:
    """Analyze image files and describe their content."""
    try:
        from PIL import Image
        
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' not found."
            
        with Image.open(filepath) as img:
            width, height = img.size
            format_type = img.format
            mode = img.mode
            
            analysis = f"""
Image Analysis Results:
- Dimensions: {width} x {height} pixels
- Format: {format_type}
- Color Mode: {mode}
- File Size: {os.path.getsize(filepath)} bytes
- File Path: {filepath}
"""
            return analysis
            
    except ImportError:
        return "Error: PIL library required. Install with: pip install Pillow"
    except Exception as e:
        return f"Error analyzing image '{filepath}': {e}"

@mcp.tool()
def search_files(directory: str, keyword: str) -> str:
    """Searches for files containing a specific keyword within a directory."""
    found_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        if keyword in f.read():
                            found_files.append(filepath)
                except:
                    pass
        if found_files:
            return f"Files containing '{keyword}':\n" + "\n".join(found_files)
        else:
            return f"No files found containing '{keyword}'"
    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."

@mcp.tool()
def analyze_image_with_claude(filepath: str) -> str:
    """Analyze image content using Claude's vision capabilities."""
    try:
        with open(filepath, 'rb') as f:
            image_bytes = f.read()
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        return f"""
IMAGE_READY_FOR_ANALYSIS:
Filename: {os.path.basename(filepath)}
File Size: {len(image_bytes)} bytes
Base64 Data (first 100 chars): {base64_data[:100]}...

Use this image data with a multimodal model like Claude to analyze the visual content.
"""
    except Exception as e:
        return f"Error processing image: {e}"

# --- NEW MEDICATION TOOLS (FastMCP compatible) ---
@mcp.tool()
def get_medication_logs(days: int = 7) -> str:
    """Get recent medication dose logs from the database."""
    try:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT m.name, l.taken_at 
            FROM dose_logs l
            JOIN medications m ON l.medication_id = m.id
            WHERE DATE(l.taken_at) >= DATE(?)
            ORDER BY l.taken_at DESC
        ''', (cutoff_date,))
        
        logs = c.fetchall()
        conn.close()
        
        if not logs:
            return f"No medication logs found in the last {days} days."
        
        result = f"Medication logs for the last {days} days:\n\n"
        for name, taken_at in logs:
            result += f"• {name} taken at {taken_at}\n"
        
        return result
        
    except Exception as e:
        return f"Error reading medication logs: {e}"

@mcp.tool()
def check_medication_schedule() -> str:
    """Check today's medication schedule based on frequency."""
    try:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        
        c.execute("SELECT name, dosage, frequency FROM medications")
        medications = c.fetchall()
        conn.close()
        
        if not medications:
            return "No medications in your schedule."
        
        result = "Today's Medication Schedule:\n\n"
        
        for name, dosage, frequency in medications:
            result += f"• {name}"
            if dosage:
                result += f" ({dosage})"
            if frequency:
                result += f" - {frequency}"
            result += "\n"
        
        # Check for missed doses today
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        c.execute('''
            SELECT m.name 
            FROM medications m
            WHERE NOT EXISTS (
                SELECT 1 FROM dose_logs l 
                WHERE l.medication_id = m.id 
                AND DATE(l.taken_at) = DATE('now')
            )
        ''')
        missed = [row[0] for row in c.fetchall()]
        conn.close()
        
        if missed:
            result += f"\n⚠️ Missed today: {', '.join(missed)}"
        
        return result
        
    except Exception as e:
        return f"Error checking schedule: {e}"

@mcp.tool()
def export_health_report(directory: str = ".") -> str:
    """Export a health report with medication history."""
    try:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        
        # Get all data
        c.execute("SELECT * FROM medications")
        medications = c.fetchall()
        
        c.execute('''
            SELECT m.name, l.taken_at 
            FROM dose_logs l
            JOIN medications m ON l.medication_id = m.id
            ORDER BY l.taken_at DESC
        ''')
        dose_history = c.fetchall()
        conn.close()
        
        # Create report
        report = {
            "generated_at": datetime.datetime.now().isoformat(),
            "medications": [
                {
                    "id": med[0],
                    "name": med[1],
                    "dosage": med[2],
                    "frequency": med[3],
                    "created": med[4]
                }
                for med in medications
            ],
            "dose_history": [
                {
                    "medication": dose[0],
                    "taken_at": dose[1]
                }
                for dose in dose_history
            ],
            "summary": {
                "total_medications": len(medications),
                "total_doses": len(dose_history),
                "last_7_days": len([d for d in dose_history if 
                                   (datetime.datetime.now() - datetime.datetime.fromisoformat(d[1])).days <= 7])
            }
        }
        
        # Save to file
        filename = f"health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return f"Health report exported to: {filepath}\n\nSummary:\n- Medications: {report['summary']['total_medications']}\n- Total Doses: {report['summary']['total_doses']}\n- Last 7 Days: {report['summary']['last_7_days']}"
        
    except Exception as e:
        return f"Error exporting report: {e}"

# --- NEW SIMPLE TOOLS FOR MEDICATION AGENT ---
@mcp.tool()
def get_active_medications() -> str:
    """Get list of all active medications."""
    try:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        c.execute("SELECT name, dosage, frequency FROM medications")
        meds = c.fetchall()
        conn.close()
        
        if not meds:
            return "No active medications."
        
        result = "Active Medications:\n\n"
        for name, dosage, freq in meds:
            result += f"• {name}"
            if dosage:
                result += f" ({dosage})"
            if freq:
                result += f" - {freq}"
            result += "\n"
        
        return result
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def log_dose(medication_name: str, dose_amount: str = "") -> str:
    """Log a medication dose."""
    try:
        conn = sqlite3.connect('meds.db')
        c = conn.cursor()
        
        # Find medication
        c.execute("SELECT id FROM medications WHERE name LIKE ?", (f"%{medication_name}%",))
        result = c.fetchone()
        
        if result:
            med_id = result[0]
            c.execute(
                "INSERT INTO dose_logs (medication_id) VALUES (?)",
                (med_id,)
            )
            conn.commit()
            
            message = f"✅ Logged dose for {medication_name}"
            if dose_amount:
                message += f" ({dose_amount})"
            message += f" at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        else:
            message = f"⚠️ Medication '{medication_name}' not found"
        
        conn.close()
        return message
        
    except Exception as e:
        return f"Error logging dose: {e}"

# Entry point to run the server
if __name__ == "__main__":
    logger.info("Starting FastMCP server with medication tools...")
    logger.info("Tools available:")
    logger.info("- list_files, read_file, analyze_image, search_files")
    logger.info("- get_medication_logs, check_medication_schedule, export_health_report")
    logger.info("- get_active_medications, log_dose")
    
    # Run with SSE transport (standard for FastMCP)
    mcp.run(transport="sse", host="0.0.0.0", port=8080)