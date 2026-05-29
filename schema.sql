-- Database Schema for College FAQ Chatbot

-- 1. FAQs Table
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- Admissions, Courses, Fees, Placements, Exams, Hostel, General
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tags TEXT,                       -- Comma-separated keywords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Unanswered Queries Table
CREATE TABLE IF NOT EXISTS unanswered_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved INTEGER DEFAULT 0       -- 0 = No, 1 = Yes
);

-- 3. Analytics Table
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    matched_faq_id INTEGER,
    was_fallback INTEGER DEFAULT 0,  -- 0 = Direct NLP match, 1 = LLM Fallback
    user_feedback TEXT,              -- 'like', 'dislike', or NULL
    asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(matched_faq_id) REFERENCES faqs(id) ON DELETE SET NULL
);

-- 4. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
