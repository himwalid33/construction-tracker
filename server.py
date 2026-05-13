from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
import traceback
from datetime import datetime
import io

app = Flask(__name__)

# Enable CORS for ALL origins
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": False
    }
}, send_wildcard=True)

# Add CORS headers to ALL responses including errors
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# In-memory database for Render.com (no disk needed!)
# Data persists as long as the server is running
DB_PATH = ':memory:'  # In-memory SQLite

# For local development, use file
if os.environ.get('FLASK_ENV') != 'production':
    DB_PATH = 'construction.db'

print(f"Database mode: {'In-Memory (Render.com)' if DB_PATH == ':memory:' else 'File (Local)'}")

# Global connection for in-memory database
_db_conn = None

def get_db():
    global _db_conn
    if DB_PATH == ':memory:':
        if _db_conn is None:
            _db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _db_conn.row_factory = sqlite3.Row
            init_db_tables(_db_conn)
        return _db_conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db_tables(conn):
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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

    c.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")
    conn.commit()
    print("Database tables initialized!")

def init_db():
    try:
        print("Initializing database...")
        conn = get_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")
        print(traceback.format_exc())
        raise

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    print(f"500 Error: {error}")
    print(traceback.format_exc())
    response = jsonify({'error': 'Internal server error', 'message': str(error)})
    response.status_code = 500
    return response

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Not found'})
    response.status_code = 404
    return response

# Handle OPTIONS requests for CORS preflight
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({'status': 'ok'})

# ==================== PROJECTS API ====================
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM projects ORDER BY id')
        projects = [dict(row) for row in c.fetchall()]
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify(projects)
    except Exception as e:
        print(f"Error in get_projects: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:id>', methods=['GET'])
def get_project(id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM projects WHERE id = ?', (id,))
        row = c.fetchone()
        if DB_PATH != ':memory:':
            conn.close()
        if row:
            return jsonify(dict(row))
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        print(f"Error in get_project: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'id': project_id, 'message': 'Project created successfully'})
    except Exception as e:
        print(f"Error in create_project: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Project updated successfully'})
    except Exception as e:
        print(f"Error in update_project: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM payments WHERE project_id = ?', (id,))
        c.execute('DELETE FROM projects WHERE id = ?', (id,))
        conn.commit()
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Project deleted successfully'})
    except Exception as e:
        print(f"Error in delete_project: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CONTRACTORS API ====================
@app.route('/api/contractors', methods=['GET'])
def get_contractors():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM contractors ORDER BY id')
        contractors = [dict(row) for row in c.fetchall()]
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify(contractors)
    except Exception as e:
        print(f"Error in get_contractors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contractors', methods=['POST'])
def create_contractor():
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'id': contractor_id, 'message': 'Contractor created successfully'})
    except Exception as e:
        print(f"Error in create_contractor: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contractors/<int:id>', methods=['PUT'])
def update_contractor(id):
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Contractor updated successfully'})
    except Exception as e:
        print(f"Error in update_contractor: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contractors/<int:id>', methods=['DELETE'])
def delete_contractor(id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE projects SET contractor_id = NULL WHERE contractor_id = ?', (id,))
        c.execute('DELETE FROM contractors WHERE id = ?', (id,))
        conn.commit()
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Contractor deleted successfully'})
    except Exception as e:
        print(f"Error in delete_contractor: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== PAYMENTS API ====================
@app.route('/api/payments', methods=['GET'])
def get_payments():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM payments ORDER BY date DESC')
        payments = [dict(row) for row in c.fetchall()]
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify(payments)
    except Exception as e:
        print(f"Error in get_payments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def create_payment():
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'id': payment_id, 'message': 'Payment created successfully'})
    except Exception as e:
        print(f"Error in create_payment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:id>', methods=['PUT'])
def update_payment(id):
    try:
        data = request.get_json() or {}
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
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Payment updated successfully'})
    except Exception as e:
        print(f"Error in update_payment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM payments WHERE id = ?', (id,))
        conn.commit()
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Payment deleted successfully'})
    except Exception as e:
        print(f"Error in delete_payment: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== SETTINGS API ====================
@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM settings WHERE id = 1')
        row = c.fetchone()
        settings = dict(row) if row else {'retainage_percent': 5, 'currency': 'SAR', 'alert_days': 7}
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify(settings)
    except Exception as e:
        print(f"Error in get_settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    try:
        data = request.get_json() or {}
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            UPDATE settings SET 
                retainage_percent = ?, currency = ?, alert_days = ?
            WHERE id = 1
        """, (data.get('retainage_percent', 5), data.get('currency', 'SAR'), data.get('alert_days', 7)))
        conn.commit()
        if DB_PATH != ':memory:':
            conn.close()
        return jsonify({'message': 'Settings updated successfully'})
    except Exception as e:
        print(f"Error in update_settings: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== STATISTICS API ====================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT COUNT(*) as count FROM projects')
        total_projects = c.fetchone()['count']

        c.execute('SELECT SUM(budget) as total FROM projects')
        total_budget = c.fetchone()['total'] or 0

        c.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'paid'")
        total_paid = c.fetchone()['total'] or 0

        total_remaining = total_budget - total_paid

        if DB_PATH != ':memory:':
            conn.close()

        return jsonify({
            'total_projects': total_projects,
            'total_budget': total_budget,
            'total_paid': total_paid,
            'total_remaining': total_remaining,
            'progress': round((total_paid / total_budget * 100), 1) if total_budget > 0 else 0
        })
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== BACKUP/RESTORE API (for Render.com in-memory DB) ====================
@app.route('/api/backup', methods=['GET'])
def backup_database():
    """Export all data as JSON for backup"""
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM projects')
        projects = [dict(row) for row in c.fetchall()]

        c.execute('SELECT * FROM contractors')
        contractors = [dict(row) for row in c.fetchall()]

        c.execute('SELECT * FROM payments')
        payments = [dict(row) for row in c.fetchall()]

        if DB_PATH != ':memory:':
            conn.close()

        return jsonify({
            'projects': projects,
            'contractors': contractors,
            'payments': payments,
            'export_date': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error in backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/restore', methods=['POST'])
def restore_database():
    """Import data from JSON backup"""
    try:
        data = request.get_json() or {}
        conn = get_db()
        c = conn.cursor()

        # Clear existing data
        c.execute('DELETE FROM payments')
        c.execute('DELETE FROM projects')
        c.execute('DELETE FROM contractors')

        # Import contractors
        for contractor in data.get('contractors', []):
            c.execute("""
                INSERT INTO contractors (id, name, company, phone, email, address, cr, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (contractor.get('id'), contractor.get('name'), contractor.get('company'),
                  contractor.get('phone'), contractor.get('email'), contractor.get('address'),
                  contractor.get('cr'), contractor.get('status', 'active'), contractor.get('notes')))

        # Import projects
        for project in data.get('projects', []):
            c.execute("""
                INSERT INTO projects (id, name, type, contractor_id, budget, start_date, end_date, location, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project.get('id'), project.get('name'), project.get('type'),
                  project.get('contractor_id'), project.get('budget', 0),
                  project.get('start_date'), project.get('end_date'),
                  project.get('location'), project.get('status', 'active'), project.get('notes')))

        # Import payments
        for payment in data.get('payments', []):
            c.execute("""
                INSERT INTO payments (id, project_id, contractor_id, phase, amount, date, method, retainage, description, docs, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (payment.get('id'), payment.get('project_id'), payment.get('contractor_id'),
                  payment.get('phase'), payment.get('amount', 0), payment.get('date'),
                  payment.get('method', 'transfer'), payment.get('retainage', 5),
                  payment.get('description'), payment.get('docs'), payment.get('status', 'paid')))

        conn.commit()
        if DB_PATH != ':memory:':
            conn.close()

        return jsonify({'message': 'Database restored successfully'})
    except Exception as e:
        print(f"Error in restore: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ==================== SERVE FRONTEND ====================
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# ==================== MAIN ====================
if __name__ == '__main__':
    try:
        init_db()

        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('FLASK_ENV') != 'production'

        print("=" * 60)
        print("Construction Tracker Server")
        print("=" * 60)
        print(f"Server running on: http://0.0.0.0:{port}")
        print(f"Database mode: {'In-Memory (Render.com)' if DB_PATH == ':memory:' else 'File (Local)'}")
        print("=" * 60)

        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        print(traceback.format_exc())
