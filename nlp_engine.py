import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sqlite3
import re
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API dynamically with try-except to support Python 3.14 compatibility
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_AVAILABLE = False
genai = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        print("Gemini API enabled in NLP Engine.")
    except Exception as e:
        print(f"Warning: Gemini API disabled due to system library compatibility: {e}")
        print("NLP Engine will run in offline-only mode.")
else:
    print("Gemini API key not found. NLP Engine running in offline-only mode.")


DB_PATH = 'database.db'

# Simple list of English stopwords to improve matching accuracy
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 
    'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 
    'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 
    'weren', 'won', 'wouldn'
}

def clean_text(text):
    """Lowercase, strip punctuation, and tokenize."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    return tokens

def stem_word(word):
    """Simple suffix stemming rule to handle basic plurals and gerunds."""
    if len(word) <= 4:
        return word
    if word.endswith('sses'):
        return word[:-2]
    if word.endswith('ies'):
        return word[:-3] + 'i'
    if word.endswith('ss'):
        return word
    if word.endswith('s') and not word.endswith('us') and not word.endswith('is') and not word.endswith('as'):
        return word[:-1]
    if word.endswith('eed'):
        return word[:-1]
    if word.endswith('ing'):
        return word[:-3]
    if word.endswith('ed'):
        return word[:-2]
    return word

def preprocess_text(text):
    """Cleans, tokenizes, filters stopwords, and stems words."""
    tokens = clean_text(text)
    processed = [stem_word(t) for t in tokens if t not in STOPWORDS]
    return processed

def get_all_faqs():
    """Fetch all FAQs from the SQLite database."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, question, answer, tags FROM faqs")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_all_faqs: {e}")
        return []

class TFIDFMatcher:
    def __init__(self, faqs):
        self.faqs = faqs
        self.vocab = set()
        self.doc_tokens = []
        self.doc_vectors = []
        self.idf = {}
        
        # Preprocess each FAQ question & tags
        for faq in faqs:
            # Combine question and tags (tags get doubled weight for importance)
            q_tokens = preprocess_text(faq['question'])
            tag_tokens = preprocess_text(faq['tags'] if faq['tags'] else '')
            # Double count tags to boost their significance in matching
            combined = q_tokens + tag_tokens + tag_tokens
            self.doc_tokens.append(combined)
            for t in combined:
                self.vocab.add(t)
                
        self.vocab = list(self.vocab)
        self.vocab_indices = {word: i for i, word in enumerate(self.vocab)}
        
        # Calculate IDF
        num_docs = len(faqs)
        for word in self.vocab:
            df = sum(1 for tokens in self.doc_tokens if word in tokens)
            self.idf[word] = math.log(1 + (num_docs / (df if df > 0 else 1)))
            
        # Build vectors for each document
        for tokens in self.doc_tokens:
            vec = [0.0] * len(self.vocab)
            tf_counts = {}
            for t in tokens:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            
            for t, count in tf_counts.items():
                if t in self.vocab_indices:
                    idx = self.vocab_indices[t]
                    tf = count / len(tokens)
                    vec[idx] = tf * self.idf[t]
                    
            # Normalize vector to unit length (L2 norm)
            norm = math.sqrt(sum(v**2 for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            self.doc_vectors.append(vec)

    def calculate_similarity(self, query):
        """Finds cosine similarity between query and FAQ documents."""
        q_tokens = preprocess_text(query)
        if not q_tokens or not self.vocab:
            return []
            
        # Build query vector
        q_vec = [0.0] * len(self.vocab)
        q_tf = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
            
        for t, count in q_tf.items():
            if t in self.vocab_indices:
                idx = self.vocab_indices[t]
                tf = count / len(q_tokens)
                q_vec[idx] = tf * self.idf[t]
                
        # Normalize query vector
        q_norm = math.sqrt(sum(v**2 for v in q_vec))
        if q_norm == 0:
            return []
        q_vec = [v / q_norm for v in q_vec]
        
        # Calculate cosine similarity with all doc vectors
        scores = []
        for i, doc_vec in enumerate(self.doc_vectors):
            dot_product = sum(q_vec[j] * doc_vec[j] for j in range(len(self.vocab)))
            
            # Tag keyword matching boost
            faq = self.faqs[i]
            tag_list = preprocess_text(faq['tags'] if faq['tags'] else '')
            matched_tags = set(q_tokens).intersection(set(tag_list))
            boost = len(matched_tags) * 0.12  # Add 0.12 boost for each matching keyword tag
            
            final_score = min(dot_product + boost, 1.0)
            scores.append((i, final_score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

def query_chatbot(user_query):
    """
    Core function called by the API.
    1. Runs offline TF-IDF similarity matcher.
    2. Logs unanswered queries if low similarity.
    3. Triggers Gemini API fallback if key is configured, providing official context.
    """
    # Special query to list counts
    if user_query == "system_load_faqs_list":
        return {
            "answer": "System catalog loaded.",
            "category": "System",
            "matched_faq_id": None,
            "was_fallback": False,
            "confidence": 1.0,
            "suggestions": []
        }

    faqs = get_all_faqs()
    if not faqs:
        return {
            "answer": "I apologize, but my FAQ database appears to be empty at the moment. Please contact the administrator.",
            "category": "System",
            "matched_faq_id": None,
            "was_fallback": False,
            "confidence": 0.0,
            "suggestions": []
        }
        
    matcher = TFIDFMatcher(faqs)
    similarity_scores = matcher.calculate_similarity(user_query)
    
    # Define a similarity threshold
    CONFIDENCE_THRESHOLD = 0.22
    
    # Get top match
    best_match = None
    best_score = 0.0
    
    if similarity_scores:
        idx, best_score = similarity_scores[0]
        if best_score >= CONFIDENCE_THRESHOLD:
            best_match = faqs[idx]
            
    # Gather other category suggestions for interactive follow-up
    suggestions = []
    if best_match:
        category = best_match['category']
        cat_faqs = [f for f in faqs if f['category'] == category and f['id'] != best_match['id']]
        suggestions = [f['question'] for f in cat_faqs[:3]]
    else:
        suggestions = [
            "How do I apply for admissions?",
            "What is the annual tuition fee for B.Tech CSE?",
            "What are the hostel rules and curfew timings?"
        ]

    # --- GEMINI DYNAMIC AI FALLBACK OPTION
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            # Build high-quality context from the top 3 matches
            context_str = ""
            limit = min(3, len(similarity_scores))
            for rank in range(limit):
                idx_rank, score_rank = similarity_scores[rank]
                faq_rank = faqs[idx_rank]
                context_str += f"Category: {faq_rank['category']}\nQuestion: {faq_rank['question']}\nAnswer: {faq_rank['answer']}\n(Relevance Score: {score_rank:.2f})\n\n"
                
            # Try a list of supported Gemini models for compatibility
            model_names = [
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro",
                "gemini-1.0-pro"
            ]
            model = None
            for mn in model_names:
                try:
                    model = genai.GenerativeModel(mn)
                    break
                except Exception as me:
                    # Continue to next model if current one is unavailable
                    print(f"Gemini model {mn} not available: {me}")
            if model is None:
                raise RuntimeError("No compatible Gemini model found.")

            prompt = f"""
You are "College Assistant Bot", an friendly, intelligent, and virtual assistant designed to answer FAQs for our College. 

Your goal is to provide a structured, helpful, and concise answer to the student's query using the Official College FAQ Database details provided below.

--- OFFICIAL FAQ CONTEXT ---
{context_str}
---------------------------

STUDENT QUERY: "{user_query}"

Instructions:
1. If the context contains the answer (relevance score > 0.20), formulate a neat, structured, and warm response incorporating these facts. Present details plainly without markdown formatting. **Do NOT start the answer with a greeting such as "Hello" or "Hi".**
2. If the context does not contain the answer, you can politely reply using your general college-advising knowledge, but clearly mention it as general guidance and invite them to ask the Admissions/Academic Cell at info@college.edu or check their student portal.
3. Be professional, direct, and warm. Avoid rambling. Limit your response to 3-4 concise sentences or a structured list.
"""
            response = model.generate_content(prompt)
            ai_answer = response.text.strip()
            
            matched_id = best_match['id'] if best_match else None
            
            if best_score < CONFIDENCE_THRESHOLD:
                log_unanswered_query(user_query)
                
            return {
                "answer": ai_answer,
                "category": best_match['category'] if best_match else "AI Assistant",
                "matched_faq_id": matched_id,
                "was_fallback": True,
                "confidence": float(best_score),
                "suggestions": suggestions
            }
        except Exception as e:
            error_msg = f"Gemini API Error: {e}. Falling back to offline TF-IDF match."
            print(error_msg)
            # Return response indicating fallback attempted but failed, preserving was_fallback flag
            return {
                "answer": error_msg,
                "category": "AI Assistant",
                "matched_faq_id": None,
                "was_fallback": True,
                "confidence": float(best_score),
                "suggestions": suggestions
            }
    # --- OFFLINE/FALLBACK RESPONSE GENERATION ---
    if best_match:
        return {
            "answer": best_match['answer'],
            "category": best_match['category'],
            "matched_faq_id": best_match['id'],
            "was_fallback": False,
            "confidence": float(best_score),
            "suggestions": suggestions
        }
    else:
        log_unanswered_query(user_query)
        fallback_msg = (
            "I'm sorry, I couldn't find an exact answer to your query in my database. "
            "I have logged this question for our college administrators to review and update in our records. "
            "For urgent assistance, please contact our helpline at +1 (555) 019-2830 or email info@college.edu."
        )
        return {
            "answer": fallback_msg,
            "category": "Unmatched",
            "matched_faq_id": None,
            "was_fallback": False,
            "confidence": float(best_score),
            "suggestions": suggestions
        }

def log_unanswered_query(query):
    """Log an unanswered query to SQLite for administrative review."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM unanswered_queries WHERE query = ? AND resolved = 0", (query,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO unanswered_queries (query) VALUES (?)", (query,))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging unanswered query: {e}")
