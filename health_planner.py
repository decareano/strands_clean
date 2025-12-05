# health_planner.py - Health Planning Agent
import datetime

class HealthPlanner:
    """Simple health planning agent"""
    
    def __init__(self):
        self.plans = {}
    
    def create_plan(self, user_id, goal, medications):
        """Create a health plan"""
        plan_id = f"plan_{len(self.plans) + 1}"
        
        # Simple rule-based plans
        if "blood pressure" in goal.lower():
            steps = [
                "Measure blood pressure daily",
                "Take medications as prescribed",
                "Reduce sodium intake",
                "Exercise 30 minutes daily",
                "Follow up with doctor in 1 month"
            ]
        elif "diabetes" in goal.lower():
            steps = [
                "Check blood sugar morning and evening",
                "Take medications with meals",
                "Monitor carbohydrate intake",
                "Stay hydrated",
                "Schedule eye exam annually"
            ]
        elif "weight" in goal.lower():
            steps = [
                "Track meals daily",
                "Exercise 150 minutes per week",
                "Weigh weekly",
                "Get 7-8 hours sleep",
                "Drink 8 glasses of water daily"
            ]
        else:
            steps = [
                f"Take medications: {medications}",
                "Track symptoms daily",
                "Schedule doctor appointment",
                "Get adequate rest",
                "Maintain healthy diet"
            ]
        
        plan = {
            "id": plan_id,
            "goal": goal,
            "steps": steps,
            "created": datetime.datetime.now().strftime("%Y-%m-%d"),
            "progress": 0,
            "completed_steps": []
        }
        
        self.plans[plan_id] = plan
        return plan
    
    def update_progress(self, plan_id, step):
        """Update plan progress"""
        if plan_id in self.plans:
            if step not in self.plans[plan_id]["completed_steps"]:
                self.plans[plan_id]["completed_steps"].append(step)
            
            total = len(self.plans[plan_id]["steps"])
            completed = len(self.plans[plan_id]["completed_steps"])
            self.plans[plan_id]["progress"] = int((completed / total) * 100)
    
    def get_suggestion(self, user_id):
        """Get a suggestion"""
        for plan_id, plan in self.plans.items():
            if plan["progress"] < 100:
                for step in plan["steps"]:
                    if step not in plan.get("completed_steps", []):
                        return f"Next step for '{plan['goal']}': {step}"
        
        return "Set a new health goal to get started!"