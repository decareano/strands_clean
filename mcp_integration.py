# mcp_integration.py - MCP Client Integration
import requests
import json
import os
import sqlite3
import datetime

class FileMCPClient:
    """Client for MCP file server"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.connected = False
        self._test_connection()
    
    def _test_connection(self):
        """Test if MCP server is running"""
        try:
            # Simple connection test
            response = requests.get(f"{self.base_url}", timeout=2)
            self.connected = response.status_code < 500
        except:
            self.connected = False
    
    def call_tool(self, tool_name, **kwargs):
        """Call an MCP tool"""
        if not self.connected:
            return self._local_fallback(tool_name, kwargs)
        
        try:
            # For FastMCP, tools are typically POST endpoints
            response = requests.post(
                f"{self.base_url}/tools/{tool_name}",
                json=kwargs,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("content", "No content")
            else:
                return f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return self._local_fallback(tool_name, kwargs, str(e))
    
    def _local_fallback(self, tool_name, args, error_msg=""):
        """Local fallback when MCP server is offline"""
        
        if tool_name == "get_medication_logs":
            days = args.get("days", 7)
            return self._get_local_logs(days)
        
        elif tool_name == "check_medication_schedule":
            return self._get_local_schedule()
        
        elif tool_name == "list_files":
            directory = args.get("directory", ".")
            try:
                files = os.listdir(directory)
                return f"Files in {directory}:\n" + "\n".join(files[:20])
            except:
                return f"Cannot list directory: {directory}"
        
        elif tool_name == "read_file":
            filepath = args.get("filepath", "")
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        return f.read()[:1000] + ("..." if os.path.getsize(filepath) > 1000 else "")
                except:
                    return f"Cannot read file: {filepath}"
            return f"File not found: {filepath}"
        
        elif tool_name == "export_health_report":
            return self._export_local_report()
        
        else:
            return f"Tool '{tool_name}' not available locally. MCP error: {error_msg}"
    
    def _get_local_logs(self, days):
        """Get local medication logs"""
        try:
            import datetime
            conn = sqlite3.connect('meds.db')
            c = conn.cursor()
            
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            c.execute('''
                SELECT m.name, l.taken_at 
                FROM dose_logs l
                JOIN medications m ON l.medication_id = m.id
                WHERE DATE(l.taken_at) >= DATE(?)
                ORDER BY l.taken_at DESC
            ''', (cutoff,))
            
            logs = c.fetchall()
            conn.close()
            
            if logs:
                result = f"Last {days} days:\n\n"
                for name, time in logs:
                    result += f"• {name} at {time}\n"
                return result
            return f"No medication logs in the last {days} days."
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    def _get_local_schedule(self):
        """Get local schedule"""
        try:
            conn = sqlite3.connect('meds.db')
            c = conn.cursor()
            c.execute("SELECT name, dosage, frequency FROM medications")
            meds = c.fetchall()
            conn.close()
            
            if meds:
                result = "Current Medications:\n\n"
                for name, dosage, freq in meds:
                    result += f"• {name}"
                    if dosage:
                        result += f" ({dosage})"
                    if freq:
                        result += f" - {freq}"
                    result += "\n"
                return result
            return "No medications in schedule."
        except Exception as e:
            return f"Error reading schedule: {str(e)}"
    
    def _export_local_report(self):
        """Export local health report"""
        try:
            import datetime
            import json
            
            conn = sqlite3.connect('meds.db')
            c = conn.cursor()
            
            # Get medications
            c.execute("SELECT * FROM medications")
            meds = c.fetchall()
            
            # Get logs
            c.execute('''
                SELECT m.name, l.taken_at 
                FROM dose_logs l
                JOIN medications m ON l.medication_id = m.id
                ORDER BY l.taken_at DESC
            ''')
            logs = c.fetchall()
            conn.close()
            
            # Create report
            report = {
                "exported_at": datetime.datetime.now().isoformat(),
                "medication_count": len(meds),
                "total_doses": len(logs),
                "recent_doses": [
                    {"medication": name, "time": time.isoformat() if hasattr(time, 'isoformat') else str(time)}
                    for name, time in logs[:10]
                ],
                "medications": [
                    {
                        "name": med[1],
                        "dosage": med[2],
                        "frequency": med[3]
                    }
                    for med in meds
                ]
            }
            
            # Save to file
            filename = f"health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            return f"Report exported to {filename}\n\nContains {len(meds)} medications and {len(logs)} dose records."
            
        except Exception as e:
            return f"Error exporting report: {str(e)}"