import json
from tah_builder import TAHBuilder

# Sample Medical Knowledge (Condensed for demonstration)
medical_data = [
    {
        "topic": "Hypertension",
        "keywords": ["Hypertension", "Blood Pressure", "Systolic", "Diastolic", "HTN"],
        "content": "Hypertension, also known as high blood pressure, is a long-term medical condition in which the blood pressure in the arteries is persistently elevated. Long-term high blood pressure is a major risk factor for coronary artery disease, stroke, heart failure, atrial fibrillation, peripheral vascular disease, vision loss, chronic kidney disease, and dementia."
    },
    {
        "topic": "Diabetes Mellitus",
        "keywords": ["Diabetes", "Insulin", "Glucose", "Hyperglycemia", "Type 1", "Type 2"],
        "content": "Diabetes mellitus, commonly known as diabetes, is a group of metabolic disorders characterized by a high blood sugar level over a prolonged period of time. Symptoms of high blood sugar include frequent urination, increased thirst, and increased hunger. If left untreated, diabetes can cause many complications."
    },
    {
        "topic": "Myocardial Infarction",
        "keywords": ["Heart Attack", "Myocardial Infarction", "Ischemia", "Coronary", "Chest Pain"],
        "content": "A myocardial infarction (MI), commonly known as a heart attack, occurs when blood flow decreases or stops to a part of the heart, causing damage to the heart muscle. The most common symptom is chest pain or discomfort which may travel into the shoulder, arm, back, neck or jaw."
    },
    {
        "topic": "Pneumonia",
        "keywords": ["Pneumonia", "Lungs", "Infection", "Alveoli", "Respiratory"],
        "content": "Pneumonia is an inflammatory condition of the lung primarily affecting the small air sacs known as alveoli. Symptoms typically include some combination of productive or dry cough, chest pain, fever and difficulty breathing. The severity of the condition is variable."
    }
    # In a real scenario, this list would have 10,000+ entries
]

def build_medical_encyclopedia():
    # Estimating 10,000 keywords for a "complete" encyclopedia
    # to ensure the Bloom filter is sized appropriately even if we only add a few shards now.
    builder = TAHBuilder(target_fp=0.0001, expected_elements=10000)
    
    print("Building Medical Encyclopedia Cartridge...")
    
    for entry in medical_data:
        builder.add_shard(entry["content"], entry["keywords"])
        # Also index the topic name
        builder._add_to_filter(entry["topic"])
        
    # Simulate adding 500 more generic medical terms to the filter to test scalability
    # (Just for sizing/FP test demonstration)
    for i in range(500):
        builder._add_to_filter(f"Term_{i}")
        
    builder.save("cartridges/medical_encyclopedia.tah")

if __name__ == "__main__":
    build_medical_encyclopedia()
