import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# Import NLP Engine functions
from nlp_engine import query_chatbot, DB_PATH

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key_12345")

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- PUBLIC ROUTES ---

@app.route('/')
def home():
    """Render the public chatbot user interface."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chatbot messages.
    Expects JSON: { "message": "user's text query" }
    """
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Message parameter is required."}), 400
        
    user_query = data['message'].strip()
    if not user_query:
        return jsonify({"error": "Empty message."}), 400
        
    # Get response from NLP Engine
    response_data = query_chatbot(user_query)
    
    # Log to analytics database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analytics (query, matched_faq_id, was_fallback)
            VALUES (?, ?, ?)
            """,
            (user_query, response_data['matched_faq_id'], 1 if response_data['was_fallback'] else 0)
        )
        # Get the ID of the inserted analytics row to return to the client
        analytics_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add analytics ID to response so client can submit feedback
        response_data['analytics_id'] = analytics_id
    except Exception as e:
        print(f"Error logging analytics: {e}")
        response_data['analytics_id'] = None
        
    return jsonify(response_data)

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """
    Submit user feedback (like/dislike) for a chat answer.
    Expects JSON: { "analytics_id": int, "feedback": "like" or "dislike" }
    """
    data = request.json
    if not data or 'analytics_id' not in data or 'feedback' not in data:
        return jsonify({"error": "Invalid feedback parameters."}), 400
        
    analytics_id = data['analytics_id']
    feedback_type = data['feedback']
    
    if feedback_type not in ['like', 'dislike']:
        return jsonify({"error": "Feedback must be 'like' or 'dislike'."}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE analytics SET user_feedback = ? WHERE id = ?",
            (feedback_type, analytics_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Feedback submitted."})
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

# --- ADMIN ROUTES & AUTHENTICATION ---

def is_admin_logged_in():
    return 'admin_logged_in' in session

@app.route('/admin')
def admin_dashboard():
    """Serve the Admin Portal login or dashboard page."""
    if not is_admin_logged_in():
        return render_template('admin.html', login_view=True)
    return render_template('admin.html', login_view=False)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Process admin credentials and establish session."""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('admin.html', login_view=True, error="All fields are required.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin.html', login_view=True, error="Invalid username or password.")
    except Exception as e:
        return render_template('admin.html', login_view=True, error=f"Database error: {e}")

@app.route('/admin/logout')
def admin_logout():
    """Clear session and log out."""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_dashboard'))

# --- ADMIN API ENDPOINTS (Protected) ---

@app.before_request
def restrict_api_endpoints():
    """Ensure that endpoints prefixed with /api/admin require admin login."""
    if request.path.startswith('/api/admin') and not is_admin_logged_in():
        return jsonify({"error": "Unauthorized access. Please login as admin."}), 401

@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    """Retrieve summarized analytics for the Admin Panel Dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Total queries
        cursor.execute("SELECT COUNT(*) FROM analytics")
        total_queries = cursor.fetchone()[0]
        
        # 2. Match success rate (Direct + Fallback vs completely unmatched)
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE matched_faq_id IS NOT NULL")
        matched_queries = cursor.fetchone()[0]
        
        accuracy_rate = 0.0
        if total_queries > 0:
            accuracy_rate = round((matched_queries / total_queries) * 100, 1)
            
        # 3. User feedback stats
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE user_feedback = 'like'")
        likes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE user_feedback = 'dislike'")
        dislikes = cursor.fetchone()[0]
        
        # 4. Unresolved unanswered queries count
        cursor.execute("SELECT COUNT(*) FROM unanswered_queries WHERE resolved = 0")
        unresolved_queries_count = cursor.fetchone()[0]
        
        # 5. Recent queries (last 10 queries)
        cursor.execute(
            """
            SELECT a.id, a.query, a.was_fallback, a.user_feedback, a.asked_at, f.question as matched_question, f.category
            FROM analytics a
            LEFT JOIN faqs f ON a.matched_faq_id = f.id
            ORDER BY a.asked_at DESC LIMIT 10
            """
        )
        recent_queries = [dict(r) for r in cursor.fetchall()]
        
        # 6. Category-wise query count
        cursor.execute(
            """
            SELECT f.category, COUNT(a.id) as count
            FROM analytics a
            JOIN faqs f ON a.matched_faq_id = f.id
            GROUP BY f.category
            """
        )
        category_stats = {r['category']: r['count'] for r in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            "total_queries": total_queries,
            "accuracy_rate": accuracy_rate,
            "likes": likes,
            "dislikes": dislikes,
            "unresolved_queries_count": unresolved_queries_count,
            "recent_queries": recent_queries,
            "category_stats": category_stats
        })
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

# REST API CRUD for FAQs
@app.route('/api/admin/faqs', methods=['GET', 'POST'])
def manage_faqs():
    """Retrieve all FAQs or create a new FAQ."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT id, category, question, answer, tags, created_at FROM faqs ORDER BY category, id DESC")
        faqs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(faqs)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get('category') or not data.get('question') or not data.get('answer'):
            return jsonify({"error": "Category, Question, and Answer are required."}), 400
            
        try:
            cursor.execute(
                "INSERT INTO faqs (category, question, answer, tags) VALUES (?, ?, ?, ?)",
                (data['category'], data['question'], data['answer'], data.get('tags', ''))
            )
            conn.commit()
            faq_id = cursor.lastrowid
            conn.close()
            return jsonify({"success": True, "message": "FAQ created successfully.", "id": faq_id}), 21
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/api/admin/faqs/<int:faq_id>', methods=['PUT', 'DELETE'])
def modify_faq(faq_id):
    """Update or delete an existing FAQ."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify FAQ exists
    cursor.execute("SELECT id FROM faqs WHERE id = ?", (faq_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "FAQ not found."}), 404
        
    if request.method == 'PUT':
        data = request.json
        if not data or not data.get('category') or not data.get('question') or not data.get('answer'):
            conn.close()
            return jsonify({"error": "Category, Question, and Answer are required."}), 400
            
        try:
            cursor.execute(
                "UPDATE faqs SET category = ?, question = ?, answer = ?, tags = ? WHERE id = ?",
                (data['category'], data['question'], data['answer'], data.get('tags', ''), faq_id)
            )
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "FAQ updated successfully."})
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Database error: {e}"}), 500
            
    elif request.method == 'DELETE':
        try:
            cursor.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "FAQ deleted successfully."})
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Database error: {e}"}), 500

# CRUD for Unanswered queries
@app.route('/api/admin/unanswered', methods=['GET'])
def get_unanswered_queries():
    """Retrieve all unresolved unanswered queries."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, query, asked_at FROM unanswered_queries WHERE resolved = 0 ORDER BY asked_at DESC")
        queries = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify(queries)
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/api/admin/unanswered/<int:query_id>/resolve', methods=['POST'])
def resolve_unanswered_query(query_id):
    """Mark an unanswered query as resolved."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE unanswered_queries SET resolved = 1 WHERE id = ?", (query_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Query marked as resolved."})
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/api/admin/unanswered/<int:query_id>', methods=['DELETE'])
def delete_unanswered_query(query_id):
    """Delete an unanswered query from the list."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM unanswered_queries WHERE id = ?", (query_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Query deleted."})
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

if __name__ == '__main__':
    # Initialize DB (creates database.db if not present)
    from db_init import init_db
    if not os.path.exists(DB_PATH):
        init_db()

    from waitress import serve
    port = int(os.getenv('PORT', '5000'))
    print(f"Starting Flask web server on port {port} with Waitress...")
    serve(app, host='0.0.0.0', port=port)
