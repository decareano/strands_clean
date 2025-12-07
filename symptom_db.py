# symptom_db.py - CORRECTED with proper diabetes symptom mapping
import requests

# CORRECTED medical symptom-to-condition mapping
MEDICAL_SYMPTOM_MAP = {
    # Diabetes & Metabolic - CORRECTED
    "extreme thirst": ["diabetes", "hyperglycemia", "dehydration"],
    "excessive thirst": ["diabetes", "hyperglycemia", "dehydration"],
    "frequent urination": ["diabetes", "urinary tract infection", "kidney disease"],
    "excessive urination": ["diabetes", "diuretic use", "kidney issues"],
    "increased hunger": ["diabetes", "hyperglycemia", "hyperthyroidism"],
    "unexplained weight loss": ["diabetes", "hyperthyroidism", "cancer"],
    "weight loss": ["diabetes", "hyperthyroidism", "cancer"],
    "blurred vision": ["diabetes", "migraine", "eye strain", "hyperglycemia"],
    "blurry vision": ["diabetes", "migraine", "eye strain", "hyperglycemia"],
    "fatigue": ["diabetes", "anemia", "depression", "chronic fatigue"],
    "tiredness": ["diabetes", "anemia", "sleep apnea", "chronic fatigue"],
    "slow healing": ["diabetes", "poor circulation", "immune deficiency"],
    "cuts slow to heal": ["diabetes", "poor circulation", "immune deficiency"],
    "frequent infections": ["diabetes", "immune deficiency", "chronic illness"],
    "tingling hands": ["diabetes", "nerve damage", "vitamin deficiency"],
    "tingling feet": ["diabetes", "nerve damage", "vitamin deficiency"],
    "numbness hands": ["diabetes", "nerve damage", "carpal tunnel"],
    "numbness feet": ["diabetes", "nerve damage", "poor circulation"],
    # Cardiovascular
    "chest pain": ["angina", "heart disease", "acid reflux", "anxiety"],
    "shortness of breath": ["asthma", "heart failure", "anemia", "anxiety"],
    "palpitations": ["arrhythmia", "anxiety", "hyperthyroidism", "anemia"],
    "swollen ankles": [
        "heart failure",
        "kidney disease",
        "circulation",
        "liver disease",
    ],
    # Gastrointestinal
    "nausea": ["gastroenteritis", "migraine", "pregnancy", "diabetes"],
    "vomiting": [
        "food poisoning",
        "migraine",
        "gastroenteritis",
        "diabetic ketoacidosis",
    ],
    "diarrhea": [
        "gastroenteritis",
        "IBS",
        "food intolerance",
        "diabetic gastroparesis",
    ],
    "constipation": [
        "IBS",
        "dehydration",
        "medication side effect",
        "diabetic neuropathy",
    ],
    "abdominal pain": ["appendicitis", "gallstones", "ulcer", "diabetic ketoacidosis"],
    # Respiratory
    "cough": ["bronchitis", "asthma", "COVID-19", "allergies"],
    "sore throat": ["pharyngitis", "strep throat", "viral infection", "allergies"],
    "runny nose": ["common cold", "allergies", "sinusitis", "viral infection"],
    "wheezing": ["asthma", "bronchitis", "allergies", "COPD"],
    # Neurological
    "headache": ["migraine", "tension headache", "sinus headache", "hyperglycemia"],
    "dizziness": ["vertigo", "low blood pressure", "anemia", "hypoglycemia"],
    "lightheaded": ["low blood pressure", "anemia", "dehydration", "hypoglycemia"],
    "numbness": [
        "pinched nerve",
        "diabetes",
        "multiple sclerosis",
        "vitamin deficiency",
    ],
    "tingling": [
        "pinched nerve",
        "diabetes",
        "vitamin deficiency",
        "nerve compression",
    ],
    # Musculoskeletal
    "joint pain": ["arthritis", "injury", "autoimmune", "diabetes"],
    "back pain": ["muscle strain", "herniated disc", "kidney issue", "poor posture"],
    "muscle pain": ["strain", "fibromyalgia", "infection", "electrolyte imbalance"],
    # Dermatological
    "rash": ["allergy", "eczema", "infection", "diabetes"],
    "itching": ["allergy", "dry skin", "liver disease", "diabetes"],
    "skin lesion": ["infection", "skin cancer", "autoimmune", "poor healing"],
    "dark skin patches": ["diabetes", "acanthosis nigricans", "hormonal imbalance"],
    "skin tags": ["diabetes", "insulin resistance", "hormonal imbalance"],
    # Hematological & Bleeding - KEEP THESE SEPARATE
    "bleeding": [
        "coagulation disorder",
        "injury",
        "medication effect",
        "liver disease",
    ],
    "easy bruising": [
        "coagulation disorder",
        "vitamin deficiency",
        "medication",
        "liver disease",
    ],
    "bruising easily": [
        "coagulation disorder",
        "vitamin deficiency",
        "medication",
        "liver disease",
    ],
    "nose bleed": ["dry air", "high blood pressure", "coagulation issue", "trauma"],
    "blood in urine": ["UTI", "kidney stones", "infection", "kidney disease"],
    "blood in stool": ["hemorrhoids", "colitis", "gastrointestinal bleed", "cancer"],
    # General & Systemic
    "fever": ["infection", "flu", "COVID-19", "inflammatory condition"],
    "fatigue": ["anemia", "depression", "chronic fatigue", "diabetes"],
    "weakness": ["anemia", "neurological issue", "electrolyte imbalance", "diabetes"],
    "chills": ["infection", "fever", "autoimmune", "anemia"],
    # Eye & Ear
    "red eye": ["conjunctivitis", "allergy", "infection", "diabetes"],
    "eye pain": ["glaucoma", "migraine", "infection", "diabetes"],
    "ear pain": ["ear infection", "sinusitis", "TMJ", "referred pain"],
    "ringing ears": [
        "tinnitus",
        "hearing loss",
        "medication side effect",
        "blood pressure",
    ],
    # Genitourinary
    "painful urination": ["UTI", "STI", "kidney stones", "diabetes"],
    "frequent urination": ["UTI", "diabetes", "prostate issues", "overactive bladder"],
    "urinary urgency": ["UTI", "overactive bladder", "prostate", "diabetes"],
    "yeast infections": [
        "diabetes",
        "hormonal imbalance",
        "antibiotic use",
        "immune issue",
    ],
    "frequent yeast infections": [
        "diabetes",
        "hormonal imbalance",
        "immune deficiency",
    ],
    # Psychiatric
    "anxiety": [
        "anxiety disorder",
        "hyperthyroidism",
        "medication",
        "blood sugar fluctuations",
    ],
    "depression": [
        "depressive disorder",
        "hormonal imbalance",
        "chronic illness",
        "diabetes",
    ],
    "irritability": [
        "blood sugar fluctuations",
        "anxiety",
        "depression",
        "hormonal changes",
    ],
    "mood swings": [
        "blood sugar fluctuations",
        "hormonal changes",
        "bipolar disorder",
        "diabetes",
    ],
    "insomnia": ["anxiety", "depression", "sleep apnea", "restless legs"],
}


def get_medications_for_symptoms(symptoms_text):
    # print(f"\n=== DEBUG: Searching for '{symptoms_text}' ===")

    symptoms_lower = symptoms_text.lower().strip()
    # print(f"Lowercase version: '{symptoms_lower}'")

    # Check mapping
    if symptoms_lower in MEDICAL_SYMPTOM_MAP:
        conditions = MEDICAL_SYMPTOM_MAP[symptoms_lower]

    else:
        # print(f"❌ No mapping found for '{symptoms_lower}'")
        conditions = [symptoms_text]

    """FIXED: Simple lookup + FDA search"""
    if not symptoms_text or not symptoms_text.strip():
        return []

    symptoms_lower = symptoms_text.lower().strip()

    # STEP 1: Check mapping FIRST
    if symptoms_lower in MEDICAL_SYMPTOM_MAP:
        conditions = MEDICAL_SYMPTOM_MAP[symptoms_lower]
        # print(f"✅ MAPPING FOUND: '{symptoms_lower}' → {conditions}")
    else:
        # No mapping found, search for the symptom directly
        conditions = [symptoms_text]
        # print(f"⚠️  No mapping, searching directly for: '{symptoms_text}'")

    # STEP 2: Search FDA for EACH condition
    all_medications = []

    for condition in conditions:
        # print(f"🔍 Searching FDA for: '{condition}'")

        try:
            # SIMPLE FDA API call
            response = requests.get(
                f'https://api.fda.gov/drug/label.json?search=purpose:"{condition}"&limit=3',
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                # print(f"   Found {len(results)} results for '{condition}'")

                for result in results:
                    # Get medication name
                    brand = result["openfda"].get("brand_name", ["Generic medication"])[
                        0
                    ]

                    # Get purpose/description
                    purpose = result.get("purpose", ["No description"])[0]

                    all_medications.append(
                        {
                            "name": brand,
                            "purpose": (
                                purpose[:150] + "..." if len(purpose) > 150 else purpose
                            ),
                            "condition": condition,
                            "source": "FDA Condition Search",
                        }
                    )
            else:
                print(f"   ❌ FDA API error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error searching for '{condition}': {e}")
            continue

    print(f"📊 Total medications found: {len(all_medications)}")
    return all_medications[:15]  # Return up to 8 results


# Test function
def test_diabetes_mapping():
    """Test diabetes symptom mapping"""
    print("🧪 Testing Diabetes Symptom Detection:\n")

    test_cases = [
        "extreme thirst and frequent urination",
        "bleeding from cut",
        "blurred vision and fatigue",
        "unexplained weight loss with increased hunger",
        "tingling in hands and feet",
        "slow healing cuts",
    ]

    for symptoms in test_cases:
        print(f"🔍 Symptoms: '{symptoms}'")
        results = get_medications_for_symptoms(symptoms)

        print(f"   Results: {len(results)}")

        for i, med in enumerate(results[:3], 1):
            if isinstance(med, dict):
                print(f"   {i}. {med.get('name', 'Generic Medication')}")
                if med.get("condition"):
                    print(f"      Condition: {med['condition']}")
                if med.get("purpose"):
                    purpose = (
                        med["purpose"][:80] + "..."
                        if len(med["purpose"]) > 80
                        else med["purpose"]
                    )
                    print(f"      Purpose: {purpose}")
            else:
                print(f"   {i}. {med}")
        print()


if __name__ == "__main__":
    test_diabetes_mapping()
