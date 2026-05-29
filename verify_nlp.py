import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sqlite3
from db_init import init_db
from nlp_engine import query_chatbot, DB_PATH

def test_system():
    print("==================================================")
    print("  AI College FAQ Chatbot - NLP Engine Verification ")
    print("==================================================")
    
    # 1. Initialize DB if not present or reset
    if os.path.exists(DB_PATH):
        print(f"Database '{DB_PATH}' exists. Resetting for test...")
        os.remove(DB_PATH)
        
    init_db()
    
    # Verify records exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM faqs")
    count = cursor.fetchone()[0]
    print(f"Total seeded FAQs in database: {count}")
    conn.close()
    
    assert count > 0, "Error: FAQs table is empty!"

    # 2. Run Test Queries
    test_queries = [
        "How can I apply for admission?",
        "what is the tuition fee for engineering computer science?",
        "Are there any scholarship criteria?",
        "hostel mess food quality?",
        "when are the exams?",
        "tell me about placement achievements",
        "can I fly a helicopter on campus?"  # Unmatched query
    ]

    print("\n--- Running Test Queries ---")
    for q in test_queries:
        print(f"\nUser Query: '{q}'")
        res = query_chatbot(q)
        print(f"Matched Category: {res['category']}")
        print(f"Confidence Score: {res['confidence']:.4f}")
        print(f"Fallback Mode (Gemini): {res['was_fallback']}")
        print(f"Matched FAQ ID: {res['matched_faq_id']}")
        print(f"Bot Answer Preview: {res['answer'][:120]}...")
        
        # Verify confidence threshold logic
        if q == "can I fly a helicopter on campus?":
            assert res['matched_faq_id'] is None, "Error: Helicopter query should not match database FAQs!"
            print("[OK] Correctly classified as Unmatched (score below threshold).")
        else:
            assert res['matched_faq_id'] is not None, f"Error: '{q}' should have matched a database FAQ!"
            print(f"[OK] Correctly matched FAQ ID {res['matched_faq_id']}.")

    print("\n==================================================")
    print("  NLP Similarity Verification PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    test_system()
