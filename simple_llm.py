# simple_llm.py - Simple LLM Wrapper
import os

class SimpleMedAI:
    """Simple AI for medical reasoning"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.has_llm = bool(self.api_key)
        
        if self.has_llm:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.model = "gpt-3.5-turbo"
            except ImportError:
                self.has_llm = False
    
    def analyze_symptoms(self, symptoms_text, user_medications=None):
        """Analyze symptoms with AI"""
        if not self.has_llm:
            return self._basic_analysis(symptoms_text, user_medications)
        
        try:
            prompt = self._build_prompt(symptoms_text, user_medications)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful medical AI assistant. Be cautious and always recommend consulting a doctor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception:
            return self._basic_analysis(symptoms_text, user_medications)
    
    def _build_prompt(self, symptoms, medications):
        """Build AI prompt"""
        prompt = f"The user describes these symptoms: {symptoms}\n\n"
        
        if medications:
            prompt += f"They are currently taking: {', '.join(medications)}\n\n"
        
        prompt += """Please provide:
1. Possible over-the-counter medications to consider
2. When to see a doctor
3. One self-care tip

Keep it brief and clear."""
        
        return prompt
    
    def _basic_analysis(self, symptoms, medications):
        """Basic analysis without AI"""
        analysis = f"**Symptoms:** {symptoms}\n\n"
        
        if medications:
            analysis += f"**Current medications:** {', '.join(medications)}\n\n"
        
        analysis += """**Recommendations:**
1. Consider common OTC medications based on symptoms
2. Consult a doctor if symptoms persist more than 3 days
3. Rest and stay hydrated

*Note: AI analysis unavailable. For personalized advice, consult a healthcare professional.*"""
        
        return analysis