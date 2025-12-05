# test_fda.py
import requests

def test_fda_search():
    print("Testing FDA API...")
    
    # Test 1: Search for sore throat
    response = requests.get(
        "https://api.fda.gov/drug/label.json?search=purpose:\"sore throat\"&limit=3",
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('results', []))}")
        
        for result in data.get('results', []):
            brand = result['openfda'].get('brand_name', ['Unknown'])[0]
            purpose = result.get('purpose', ['No purpose'])[0]
            print(f"\n• {brand}")
            print(f"  Purpose: {purpose[:100]}...")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_fda_search()