# med_agent.py - AI Agent with MCP tool access
from symptom_db import get_medications_for_symptoms
from simple_llm import SimpleMedAI
from health_planner import HealthPlanner
from mcp_integration import FileMCPClient

class TrueMedicationAgent:
    """TRUE AI Agent with MCP tool access"""
    
    def __init__(self, openai_key=None):
        self.llm = SimpleMedAI(openai_key)
        self.planner = HealthPlanner()
        self.user_context = {}
        
        # Connect to MCP server
        self.mcp_client = FileMCPClient("http://localhost:8080")
        
        # Available tools
        self.available_tools = [
            "get_medication_logs",
            "check_medication_schedule",
            "list_files",
            "read_file",
            "export_health_report"
        ]
    
    def analyze_symptoms(self, symptoms_text, user_medications=None):
        """Analyze symptoms with AI and FDA data"""
        if not symptoms_text or not symptoms_text.strip():
            return "Please describe your symptoms."
        
        # Try AI analysis first
        try:
            ai_analysis = self.llm.analyze_symptoms(symptoms_text, user_medications)
        except Exception:
            ai_analysis = "AI analysis unavailable. Using basic matching."
        
        # Get FDA data
        fda_results = get_medications_for_symptoms(symptoms_text)
        
        # Combine results
        return {
            "ai_analysis": ai_analysis,
            "fda_recommendations": fda_results,
            "summary": self._summarize_results(fda_results, ai_analysis)
        }
    
    def create_health_plan(self, user_id, goal, medications):
        """Create a health plan"""
        return self.planner.create_plan(user_id, goal, medications)
    
    def analyze_with_context(self, query):
        """Analyze query using MCP tools for context"""
        if not query:
            return {"error": "No query provided"}
        
        # Gather context using MCP tools
        context = {}
        
        try:
            # Get medication logs
            context["medication_logs"] = self.mcp_client.call_tool(
                "get_medication_logs", 
                days=7
            )
        except Exception as e:
            context["medication_logs"] = f"Error: {str(e)}"
        
        try:
            # Get schedule
            context["schedule"] = self.mcp_client.call_tool(
                "check_medication_schedule"
            )
        except Exception as e:
            context["schedule"] = f"Error: {str(e)}"
        
        # Analyze with AI
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        full_prompt = f"Query: {query}\n\nContext:\n{context_str}\n\nProvide analysis and recommendations."
        
        try:
            ai_response = self.llm.analyze_symptoms(full_prompt, [])
        except Exception:
            ai_response = self._simple_context_analysis(query, context)
        
        return {
            "context_gathered": context,
            "ai_analysis": ai_response,
            "tools_used": list(context.keys())
        }
    
    def _simple_context_analysis(self, query, context):
        """Simple analysis if AI fails"""
        analysis = f"**Analysis of:** {query}\n\n"
        
        if "medication_logs" in context:
            logs = context["medication_logs"]
            if "No logs" not in str(logs) and "Error" not in str(logs):
                analysis += "📊 **Based on your medication logs:**\n"
                analysis += "You have recent medication history available.\n\n"
        
        if "schedule" in context:
            schedule = context["schedule"]
            if schedule and "No medications" not in str(schedule):
                analysis += "📅 **Your current schedule:**\n"
                lines = str(schedule).split('\n')[:5]
                for line in lines:
                    analysis += f"- {line}\n"
                analysis += "\n"
        
        analysis += "💡 **Recommendation:** Continue tracking and consult with your doctor."
        
        return analysis
    
    def _summarize_results(self, fda_results, ai_analysis):
        """Summarize FDA and AI results"""
        summary = "## Summary\n\n"
        
        if isinstance(fda_results, list) and len(fda_results) > 0:
            if isinstance(fda_results[0], dict):
                meds = [med['name'] for med in fda_results[:3]]
                summary += f"**FDA Medications ({len(fda_results)} found):** {', '.join(meds)}\n\n"
            else:
                summary += f"**FDA Medications:** {', '.join(fda_results[:3])}\n\n"
        
        summary += "**AI Analysis:**\n"
        summary += ai_analysis[:300] + ("..." if len(ai_analysis) > 300 else "")
        
        return summary
    
    def log_user_action(self, user_id, action, outcome):
        """Log user action for learning"""
        if user_id not in self.user_context:
            self.user_context[user_id] = {"actions": [], "preferences": {}}
        
        self.user_context[user_id]["actions"].append({
            "action": action,
            "outcome": outcome,
            "timestamp": "now"
        })
    
    def get_personalized_tip(self, user_id):
        """Get personalized tip based on user history"""
        if user_id in self.user_context and self.user_context[user_id]["actions"]:
            actions = self.user_context[user_id]["actions"]
            
            # Simple logic: if user logs doses regularly, encourage continuation
            dose_logs = [a for a in actions if "log" in a["action"].lower() or "taken" in a["action"].lower()]
            
            if len(dose_logs) > 3:
                return "Great job with medication adherence! Keep tracking consistently."
            else:
                return "Try to log your medications daily for better health management."
        
        return "Welcome! Start by adding your medications and logging doses."