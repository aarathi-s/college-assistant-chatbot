/* ==========================================================================
   Antigravity Academic Bot - Admin Dashboard JavaScript
   ========================================================================== */

let allFaqs = [];
let allUnanswered = [];

document.addEventListener('DOMContentLoaded', () => {
    // Check if the dashboard is rendered (non-login view)
    const statsTab = document.getElementById('tab-stats');
    if (statsTab) {
        // Load initial dashboard metrics & recent logs
        loadDashboardStats();
        // Load FAQs list for management
        loadFaqList();
        // Load unanswered student queries
        loadUnansweredQueries();
    }
});

// --- Tab Switching Logic ---
function switchAdminTab(tabName) {
    // Deactivate all tabs
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar .category-btn').forEach(el => el.classList.remove('active'));
    
    // Activate selected tab
    const selectedPane = document.getElementById(`tab-${tabName}`);
    if (selectedPane) selectedPane.classList.add('active');
    
    const selectedBtn = document.getElementById(`btn-tab-${tabName}`);
    if (selectedBtn) selectedBtn.classList.add('active');
    
    // Refresh data on switch
    if (tabName === 'stats') {
        loadDashboardStats();
    } else if (tabName === 'faqs') {
        loadFaqList();
    } else if (tabName === 'unanswered') {
        loadUnansweredQueries();
    }
}

// --- Load Dashboard Analytics Statistics ---
function loadDashboardStats() {
    fetch('/api/admin/stats')
        .then(res => {
            if (res.status === 401) window.location.reload(); // Session expired
            return res.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            // Populate stats counters
            document.getElementById('stat-total-queries').innerText = data.total_queries || 0;
            document.getElementById('stat-accuracy-rate').innerText = (data.accuracy_rate || 0.0) + '%';
            document.getElementById('stat-likes').innerText = data.likes || 0;
            document.getElementById('stat-unresolved').innerText = data.unresolved_queries_count || 0;
            
            // Update sidebar counts
            const unansweredBadge = document.getElementById('badge-unanswered-total');
            if (unansweredBadge) unansweredBadge.innerText = data.unresolved_queries_count || 0;
            
            // Populate recent logs table
            populateRecentLogs(data.recent_queries || []);
        })
        .catch(err => {
            console.error("Error loading stats:", err);
        });
}

function populateRecentLogs(logs) {
    const tbody = document.getElementById('recent-logs-table-body');
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No chat sessions have been logged yet.</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    logs.forEach(log => {
        const tr = document.createElement('tr');
        
        // Match details
        const matchedText = log.matched_question 
            ? `<strong>${escapeHtml(log.matched_question)}</strong>` 
            : '<span style="color:var(--text-muted);">Unmatched Fallback</span>';
            
        // Mode badge
        const modeBadge = log.was_fallback 
            ? '<span class="badge badge-fallback">Gemini AI</span>' 
            : '<span class="badge badge-category">Offline NLP</span>';
            
        // Feedback badge
        let feedbackBadge = '<span style="color:var(--text-muted);">None</span>';
        if (log.user_feedback === 'like') {
            feedbackBadge = '<span class="badge badge-feedback-like">Helpful 👍</span>';
        } else if (log.user_feedback === 'dislike') {
            feedbackBadge = '<span class="badge badge-feedback-dislike">Unhelpful 👎</span>';
        }
        
        // Time format
        const askedAt = new Date(log.asked_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
        
        tr.innerHTML = `
            <td><span style="font-weight:500;">"${escapeHtml(log.query)}"</span><br><small style="color:var(--text-secondary);">Matched: ${matchedText}</small></td>
            <td><span class="badge badge-category">${escapeHtml(log.category || 'System')}</span></td>
            <td>${modeBadge}</td>
            <td>${feedbackBadge}</td>
            <td><small style="color:var(--text-muted);">${askedAt}</small></td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Load FAQs catalog ---
function loadFaqList() {
    fetch('/api/admin/faqs')
        .then(res => {
            if (res.status === 401) window.location.reload();
            return res.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);
            allFaqs = data;
            
            // Populate FAQs total badge
            const faqBadge = document.getElementById('badge-faq-total');
            if (faqBadge) faqBadge.innerText = allFaqs.length;
            
            renderFaqTable(allFaqs);
        })
        .catch(err => {
            console.error("Error loading FAQs:", err);
        });
}

function renderFaqTable(faqs) {
    const tbody = document.getElementById('faq-table-body');
    if (!tbody) return;
    
    if (faqs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No FAQs matching search filters were found.</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    faqs.forEach(faq => {
        const tr = document.createElement('tr');
        
        // Limit answer text preview length
        let answerPreview = faq.answer;
        if (answerPreview.length > 90) {
            answerPreview = answerPreview.substring(0, 90) + '...';
        }
        
        tr.innerHTML = `
            <td><span class="badge badge-category">${escapeHtml(faq.category)}</span></td>
            <td><strong style="font-size:0.92rem;">${escapeHtml(faq.question)}</strong></td>
            <td><span style="color:var(--text-secondary); font-size:0.88rem;">${escapeHtml(answerPreview)}</span></td>
            <td>
                <div class="action-row-btns">
                    <button class="btn-glass btn-icon btn-edit" title="Edit FAQ Record" onclick="openFaqModal(${faq.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4z"></path></svg>
                    </button>
                    <button class="btn-glass btn-icon btn-delete" title="Delete FAQ Record" onclick="deleteFaq(${faq.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Client-side Live search ---
function filterFaqTable() {
    const query = document.getElementById('faq-search-input').value.toLowerCase().trim();
    if (!query) {
        renderFaqTable(allFaqs);
        return;
    }
    
    const filtered = allFaqs.filter(faq => 
        faq.question.toLowerCase().includes(query) || 
        faq.answer.toLowerCase().includes(query) || 
        faq.category.toLowerCase().includes(query) || 
        (faq.tags && faq.tags.toLowerCase().includes(query))
    );
    renderFaqTable(filtered);
}

// --- Delete FAQ ---
function deleteFaq(faqId) {
    if (!confirm("Are you absolutely sure you want to delete this FAQ record?")) return;
    
    fetch(`/api/admin/faqs/${faqId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            loadFaqList();
        } else {
            alert("Error deleting FAQ: " + data.error);
        }
    })
    .catch(err => alert("Server error during deletion."));
}

// --- FAQ Modals Control ---
function openFaqModal(faqId = null) {
    const modal = document.getElementById('faq-modal');
    const title = document.getElementById('modal-title');
    const idField = document.getElementById('faq-id-field');
    const categoryField = document.getElementById('faq-category-field');
    const questionField = document.getElementById('faq-question-field');
    const answerField = document.getElementById('faq-answer-field');
    const tagsField = document.getElementById('faq-tags-field');
    
    if (faqId) {
        // Edit Mode
        title.innerText = "Edit FAQ Record";
        const faq = allFaqs.find(f => f.id === faqId);
        if (faq) {
            idField.value = faq.id;
            categoryField.value = faq.category;
            questionField.value = faq.question;
            answerField.value = faq.answer;
            tagsField.value = faq.tags || '';
        }
    } else {
        // Create Mode
        title.innerText = "Create New FAQ";
        idField.value = "";
        categoryField.value = "Admissions";
        questionField.value = "";
        answerField.value = "";
        tagsField.value = "";
    }
    
    modal.classList.add('active');
}

function closeFaqModal() {
    document.getElementById('faq-modal').classList.remove('active');
}

// --- Submit Modal Form ---
function submitFaqForm() {
    const id = document.getElementById('faq-id-field').value;
    const category = document.getElementById('faq-category-field').value;
    const question = document.getElementById('faq-question-field').value.trim();
    const answer = document.getElementById('faq-answer-field').value.trim();
    const tags = document.getElementById('faq-tags-field').value.trim();
    
    if (!question || !answer) {
        alert("Question and Answer fields are mandatory!");
        return;
    }
    
    const bodyData = { category, question, answer, tags };
    const url = id ? `/api/admin/faqs/${id}` : '/api/admin/faqs';
    const method = id ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            closeFaqModal();
            loadFaqList();
        } else {
            alert("Error saving FAQ: " + data.error);
        }
    })
    .catch(err => alert("Server error. Please save again."));
}

// --- Load Unanswered Queries ---
function loadUnansweredQueries() {
    fetch('/api/admin/unanswered')
        .then(res => {
            if (res.status === 401) window.location.reload();
            return res.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);
            allUnanswered = data;
            
            // Update sidebar counts
            const unansweredBadge = document.getElementById('badge-unanswered-total');
            if (unansweredBadge) unansweredBadge.innerText = allUnanswered.length;
            
            renderUnansweredList(allUnanswered);
        })
        .catch(err => {
            console.error("Error loading unanswered:", err);
        });
}

function renderUnansweredList(queries) {
    const box = document.getElementById('unanswered-queries-list');
    if (!box) return;
    
    if (queries.length === 0) {
        box.innerHTML = '<div class="empty-state">🎉 Wonderful! All student queries are successfully resolved in the FAQ database.</div>';
        return;
    }
    
    box.innerHTML = '';
    queries.forEach(q => {
        const card = document.createElement('div');
        card.className = 'unanswered-card';
        
        const askedAt = new Date(q.asked_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
        
        card.innerHTML = `
            <div class="unanswered-info">
                <h5>"${escapeHtml(q.query)}"</h5>
                <p>Logged query on: ${askedAt}</p>
            </div>
            <div class="action-row-btns">
                <button class="btn-glass" style="color:var(--accent-success);" onclick="resolveAndCreateFaq(${q.id}, '${escapeHtml(q.query).replace(/'/g, "\\'")}')">
                    Add FAQ
                </button>
                <button class="btn-glass" style="color:var(--accent-danger);" onclick="dismissUnansweredQuery(${q.id})">
                    Dismiss
                </button>
            </div>
        `;
        box.appendChild(card);
    });
}

// --- Unanswered Action Handlers ---
function resolveAndCreateFaq(queryId, queryText) {
    // 1. Open FAQ Modal prepopulated with the user query
    openFaqModal();
    document.getElementById('faq-question-field').value = queryText;
    
    // 2. Mark this query resolved upon modal submit (we intercept the submission or auto-resolve)
    // We can directly call resolution route in parallel or let admin manually clear it.
    // For ultimate convenience, let's mark it as resolved on the server right now so it disappears from lists!
    fetch(`/api/admin/unanswered/${queryId}/resolve`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            loadUnansweredQueries();
        }
    })
    .catch(err => console.error("Error resolving query:", err));
}

function dismissUnansweredQuery(queryId) {
    if (!confirm("Are you sure you want to dismiss and delete this query entry?")) return;
    
    fetch(`/api/admin/unanswered/${queryId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            loadUnansweredQueries();
        } else {
            alert("Error deleting unanswered query: " + data.error);
        }
    })
    .catch(err => alert("Server error."));
}

// --- Helper Functions ---
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
