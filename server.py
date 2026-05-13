from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r'/api/*': {'origins': '*'}})

DB_PATH = os.path.join(os.path.dirname(__file__), 'construction.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Projects table
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

    # Contractors table
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

    # Payments table
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE SET NULL
        )
    """)

    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            retainage_percent REAL DEFAULT 5,
            currency TEXT DEFAULT 'SAR',
            alert_days INTEGER DEFAULT 7
        )
    """)

    # Insert default settings
    c.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# ==================== PROJECTS API ====================
@app.route('/api/projects', methods=['GET'])
def get_projects():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM projects ORDER BY id')
    projects = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(projects)

@app.route('/api/projects/<int:id>', methods=['GET'])
def get_project(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM projects WHERE id = ?', (id,))
    project = dict(c.fetchone()) if c.fetchone else None
    conn.close()
    return jsonify(project) if project else jsonify({'error': 'Not found'}), 404

@app.route('/api/projects', methods=['POST'])
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
    return jsonify({'id': project_id, 'message': 'Project created successfully'})

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE projects SET 
            name = ?, type = ?, contractor_id = ?, budget = ?, 
            start_date = ?, end_date = ?, location = ?, status = ?, notes = ?
        WHERE id = ?
    """, (data.get('name'), data.get('type'), data.get('contractor_id'),
          data.get('budget', 0), data.get('start_date'), data.get('end_date'),
          data.get('location'), data.get('status'), data.get('notes'), id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Project updated successfully'})

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    conn = get_db()
    c = conn.cursor()
    # Payments will be deleted automatically due to CASCADE
    c.execute('DELETE FROM projects WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Project deleted successfully'})

# ==================== CONTRACTORS API ====================
@app.route('/api/contractors', methods=['GET'])
def get_contractors():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM contractors ORDER BY id')
    contractors = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(contractors)

@app.route('/api/contractors', methods=['POST'])
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
    return jsonify({'id': contractor_id, 'message': 'Contractor created successfully'})

@app.route('/api/contractors/<int:id>', methods=['PUT'])
def update_contractor(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE contractors SET 
            name = ?, company = ?, phone = ?, email = ?, 
            address = ?, cr = ?, status = ?, notes = ?
        WHERE id = ?
    """, (data.get('name'), data.get('company'), data.get('phone'),
          data.get('email'), data.get('address'), data.get('cr'),
          data.get('status'), data.get('notes'), id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contractor updated successfully'})

@app.route('/api/contractors/<int:id>', methods=['DELETE'])
def delete_contractor(id):
    conn = get_db()
    c = conn.cursor()
    # Set contractor_id to NULL in projects
    c.execute('UPDATE projects SET contractor_id = NULL WHERE contractor_id = ?', (id,))
    c.execute('DELETE FROM contractors WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Contractor deleted successfully'})

# ==================== PAYMENTS API ====================
@app.route('/api/payments', methods=['GET'])
def get_payments():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM payments ORDER BY date DESC')
    payments = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(payments)

@app.route('/api/payments', methods=['POST'])
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
    return jsonify({'id': payment_id, 'message': 'Payment created successfully'})

@app.route('/api/payments/<int:id>', methods=['PUT'])
def update_payment(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE payments SET 
            project_id = ?, contractor_id = ?, phase = ?, amount = ?, 
            date = ?, method = ?, retainage = ?, description = ?, docs = ?, status = ?
        WHERE id = ?
    """, (data.get('project_id'), data.get('contractor_id'), data.get('phase'),
          data.get('amount'), data.get('date'), data.get('method'),
          data.get('retainage'), data.get('description'), data.get('docs'),
          data.get('status'), id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Payment updated successfully'})

@app.route('/api/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM payments WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Payment deleted successfully'})

# ==================== SETTINGS API ====================
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM settings WHERE id = 1')
    settings = dict(c.fetchone()) if c.fetchone() else {'retainage_percent': 5, 'currency': 'SAR', 'alert_days': 7}
    conn.close()
    return jsonify(settings)

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE settings SET 
            retainage_percent = ?, currency = ?, alert_days = ?
        WHERE id = 1
    """, (data.get('retainage_percent', 5), data.get('currency', 'SAR'), data.get('alert_days', 7)))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Settings updated successfully'})

# ==================== STATISTICS API ====================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()

    # Total projects
    c.execute('SELECT COUNT(*) as count FROM projects')
    total_projects = c.fetchone()['count']

    # Total budget
    c.execute('SELECT SUM(budget) as total FROM projects')
    total_budget = c.fetchone()['total'] or 0

    # Total paid
    c.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'paid'")
    total_paid = c.fetchone()['total'] or 0

    # Total remaining
    total_remaining = total_budget - total_paid

    conn.close()

    return jsonify({
        'total_projects': total_projects,
        'total_budget': total_budget,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'progress': round((total_paid / total_budget * 100), 1) if total_budget > 0 else 0
    })

# ==================== SERVE FRONTEND ====================
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# For production (Render.com, Heroku, etc.)
import os

if __name__ == '__main__':
    init_db()

    # Get port from environment (Render.com sets this)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'

    print("=" * 50)
    print("Construction Tracker Server")
    print("=" * 50)
    print(f"Server running on: http://0.0.0.0:{port}")
    print("Database file: construction.db")
    print("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=debug_mode)
