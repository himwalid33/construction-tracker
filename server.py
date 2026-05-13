from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

# Enable CORS for ALL origins (required for Render.com)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'construction.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'building',
            contractor_id INTEGER,
            budget REAL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contractors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            cr TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            contractor_id INTEGER,
            phase TEXT,
            amount REAL DEFAULT 0,
            date TEXT,
            method TEXT DEFAULT 'transfer',
            retainage REAL DEFAULT 5,
            description TEXT,
            docs TEXT,
            status TEXT DEFAULT 'paid',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            retainage_percent REAL DEFAULT 5,
            currency TEXT DEFAULT 'SAR',
            alert_days INTEGER DEFAULT 7
        )
    """)

    c.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    conn.commit()
    conn.close()
    print("Database initialized!")

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ==================== API ROUTES ====================

@app.route('/api/projects', methods=['GET', 'OPTIONS'])
def get_projects():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM projects ORDER BY id')
    projects = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(projects)

@app.route('/api/projects', methods=['POST', 'OPTIONS'])
def create_project():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (name, type, contractor_id, budget, start_date, end_date, location, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('name'), data.get('type'), data.get('contractor_id'), 
          data.get('budget', 0), data.get('start_date'), data.get('end_date'),
          data.get('location'), data.get('status', 'active'), data.get('notes')))
    conn.commit()
    project_id = c.lastrowid
    conn.close()
    return jsonify({'id': project_id, 'message': 'Project created'})

@app.route('/api/projects/<int:id>', methods=['PUT', 'OPTIONS'])
def update_project(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE projects SET name=?, type=?, contractor_id=?, budget=?, 
        start_date=?, end_date=?, location=?, status=?, notes=?
        WHERE id=?
    """, (data.get('name'), data.get('type'), data.get('contractor_id'),
          data.get('budget', 0), data.get('start_date'), data.get('end_date'),
          data.get('location'), data.get('status'), data.get('notes'), id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Project updated'})

@app.route('/api/projects/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_project(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM payments WHERE project_id=?', (id,))
    c.execute('DELETE FROM projects WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Project deleted'})

@app.route('/api/contractors', methods=['GET', 'OPTIONS'])
def get_contractors():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM contractors ORDER BY id')
    contractors = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(contractors)

@app.route('/api/contractors', methods=['POST', 'OPTIONS'])
def create_contractor():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO contractors (name, company, phone, email, address, cr, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('name'), data.get('company'), data.get('phone'),
          data.get('email'), data.get('address'), data.get('cr'),
          data.get('status', 'active'), data.get('notes')))
    conn.commit()
    contractor_id = c.lastrowid
    conn.close()
    return jsonify({'id': contractor_id, 'message': 'Contractor created'})

@app.route('/api/contractors/<int:id>', methods=['PUT', 'OPTIONS'])
def update_contractor(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE contractors SET name=?, company=?, phone=?, email=?, 
        address=?, cr=?, status=?, notes=?
        WHERE id=?
    """, (data.get('name'), data.get('company'), data.get('phone'),
          data.get('email'), data.get('address'), data.get('cr'),
          data.get('status'), data.get('notes'), id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contractor updated'})

@app.route('/api/contractors/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_contractor(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE projects SET contractor_id = NULL WHERE contractor_id = ?', (id,))
    c.execute('DELETE FROM contractors WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contractor deleted'})

@app.route('/api/payments', methods=['GET', 'OPTIONS'])
def get_payments():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM payments ORDER BY date DESC')
    payments = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(payments)

@app.route('/api/payments', methods=['POST', 'OPTIONS'])
def create_payment():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (project_id, contractor_id, phase, amount, date, method, retainage, description, docs, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('project_id'), data.get('contractor_id'), data.get('phase'),
          data.get('amount', 0), data.get('date'), data.get('method', 'transfer'),
          data.get('retainage', 5), data.get('description'), data.get('docs'),
          data.get('status', 'paid')))
    conn.commit()
    payment_id = c.lastrowid
    conn.close()
    return jsonify({'id': payment_id, 'message': 'Payment created'})

@app.route('/api/payments/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_payment(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM payments WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Payment deleted'})

@app.route('/api/settings', methods=['GET', 'OPTIONS'])
def get_settings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM settings WHERE id = 1')
    row = c.fetchone()
    settings = dict(row) if row else {'retainage_percent': 5, 'currency': 'SAR', 'alert_days': 7}
    conn.close()
    return jsonify(settings)

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as count FROM projects')
    total_projects = c.fetchone()['count']
    c.execute('SELECT SUM(budget) as total FROM projects')
    total_budget = c.fetchone()['total'] or 0
    c.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'paid'")
    total_paid = c.fetchone()['total'] or 0
    conn.close()
    return jsonify({
        'total_projects': total_projects,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_remaining': total_budget - total_paid,
        'progress': round((total_paid / total_budget * 100), 1) if total_budget > 0 else 0
    })


# Add CORS headers to all responses including errors
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# Error handlers with CORS headers
@app.errorhandler(500)
def internal_error(error):
    response = jsonify({'error': 'Internal server error', 'message': str(error)})
    response.status_code = 500
    return response

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Not found'})
    response.status_code = 404
    return response

@app.errorhandler(400)
def bad_request(error):
    response = jsonify({'error': 'Bad request', 'message': str(error)})
    response.status_code = 400
    return response

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
