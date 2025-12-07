from med_agent import TrueMedicationAgent

agent = TrueMedicationAgent()

# Test if AI works
result = agent.analyze_symptoms("headache", [])
print("Result type:", type(result))
print("First 100 chars:", str(result)[:100])
