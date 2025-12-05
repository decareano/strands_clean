# symptom_db.py - ORIGINAL WORKING VERSION
import requests

def get_medications_for_symptoms(symptoms_text):
    """Search FDA database for medications by symptoms"""
    if not symptoms_text or not symptoms_text.strip():
        return ["Enter symptoms to search"]
    
    # Common symptom mapping
    symptom_map = {
        "headache": ["headache", "pain", "migraine"],
        "fever": ["fever", "temperature"],
        "pain": ["pain", "ache", "sore"],
        "cough": ["cough", "coughing"],
        "cold": ["cold", "congestion", "nasal"],
        "allergy": ["allergy", "allergic", "itch", "sneeze"],
        "inflammation": ["inflammation", "swelling"],
        "nausea": ["nausea", "vomit"],
        "heartburn": ["heartburn", "acid", "indigestion"]
    }
    
    # Find matching symptoms
    symptoms_lower = symptoms_text.lower()
    search_terms = []
    
    for symptom, keywords in symptom_map.items():
        for keyword in keywords:
            if keyword in symptoms_lower:
                search_terms.append(symptom)
                break
    
    if not search_terms:
        # Try direct search
        search_terms = [symptoms_lower.split()[0]] if symptoms_lower.split() else ["health"]
    
    # Search FDA
    medications = []
    
    for term in search_terms[:2]:  # Limit to 2 terms
        try:
            response = requests.get(
                f"https://api.fda.gov/drug/label.json?search=purpose:\"{term}\"&limit=3",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                for result in data.get("results", []):
                    brand = result["openfda"].get("brand_name", ["Unknown"])[0]
                    generic = result["openfda"].get("generic_name", ["Unknown"])[0]
                    purpose = result.get("purpose", ["No description"])[0]
                    
                    medications.append({
                        "name": brand,
                        "generic_name": generic,
                        "purpose": purpose[:100] + "..." if len(purpose) > 100 else purpose
                    })
        except Exception:
            continue
    
    # Remove duplicates
    unique_meds = []
    seen = set()
    for med in medications:
        if med["name"] not in seen:
            unique_meds.append(med)
            seen.add(med["name"])
    
    if unique_meds:
        return unique_meds[:5]  # Limit to 5 results
    
    # Fallback to basic recommendations
    return get_fallback_recommendations(search_terms)

def get_fallback_recommendations(symptoms):
    """Fallback recommendations when FDA search fails"""
    fallback_db = {
        "headache": ["Acetaminophen (Tylenol)", "Ibuprofen (Advil)", "Aspirin"],
        "fever": ["Acetaminophen (Tylenol)", "Ibuprofen (Advil)"],
        "pain": ["Acetaminophen", "Ibuprofen", "Naproxen (Aleve)"],
        "cough": ["Dextromethorphan", "Guaifenesin (Mucinex)"],
        "cold": ["Pseudoephedrine (Sudafed)", "Phenylephrine"],
        "allergy": ["Cetirizine (Zyrtec)", "Loratadine (Claritin)", "Fexofenadine (Allegra)"],
        "inflammation": ["Ibuprofen", "Naproxen"],
        "nausea": ["Dimenhydrinate (Dramamine)"],
        "heartburn": ["Famotidine (Pepcid)", "Omeprazole (Prilosec)"]
    }
    
    recommendations = []
    for symptom in symptoms:
        if symptom in fallback_db:
            recommendations.extend(fallback_db[symptom])
    
    if recommendations:
        return list(set(recommendations))[:5]
    
    return ["No specific recommendations. Consult a doctor for personalized advice."]