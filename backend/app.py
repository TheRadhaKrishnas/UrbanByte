import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import sqlite3

from config import Config
from models import (
    get_db, init_db, get_user_by_code, get_user_by_id, verify_password,
    create_user, update_user, get_complaints, create_complaint, update_complaint_status,
    get_all_users, delete_user
)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Allow cross-origin requests from frontend

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
with app.app_context():
    init_db()

# Helper to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==================== AUTHENTICATION ====================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    member_code = data.get('member_code')
    password = data.get('password')
    if not member_code or not password:
        return jsonify({'error': 'Missing credentials'}), 400

    user = get_user_by_code(member_code)
    if user and verify_password(user['password'], password):
        # Return user data (excluding password)
        user_data = {
            'id': user['id'],
            'role': user['role'],
            'member_code': user['member_code'],
            'name': user['name'],
            'flat': user['flat'],
            'phone': user['phone'],
            'email': user['email'],
            'designation': user['designation'],
            'age': user['age'],
            'gender': user['gender'],
            'family_members': user['family_members']
        }
        return jsonify({'user': user_data})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    # Validate required fields
    required = ['member_code', 'password', 'name', 'flat', 'phone', 'email']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing {field}'}), 400

    # Check if user already exists
    if get_user_by_code(data['member_code']):
        return jsonify({'error': 'Member code already exists'}), 409

    # Create new user
    user_id = create_user({
        'role': 'member',
        'member_code': data['member_code'],
        'password': data['password'],
        'name': data['name'],
        'flat': data['flat'],
        'phone': data['phone'],
        'email': data['email']
    })
    # Return created user
    user = get_user_by_id(user_id)
    user_data = {
        'id': user['id'],
        'role': user['role'],
        'member_code': user['member_code'],
        'name': user['name'],
        'flat': user['flat'],
        'phone': user['phone'],
        'email': user['email'],
        'designation': user['designation'],
        'age': user['age'],
        'gender': user['gender'],
        'family_members': user['family_members']
    }
    return jsonify({'user': user_data}), 201

# ==================== USER PROFILE ====================

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user['id'],
        'role': user['role'],
        'member_code': user['member_code'],
        'name': user['name'],
        'flat': user['flat'],
        'phone': user['phone'],
        'email': user['email'],
        'designation': user['designation'],
        'age': user['age'],
        'gender': user['gender'],
        'family_members': user['family_members']
    })

@app.route('/api/user/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    data = request.get_json()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Prepare update fields
    update_data = {}
    allowed_fields = ['name', 'flat', 'phone', 'email', 'age', 'gender', 'family_members']
    if user['role'] == 'management':
        allowed_fields.append('designation')
    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return jsonify({'error': 'No fields to update'}), 400

    if update_user(user_id, update_data):
        # Return updated user data
        updated_user = get_user_by_id(user_id)
        user_data = {
            'id': updated_user['id'],
            'role': updated_user['role'],
            'member_code': updated_user['member_code'],
            'name': updated_user['name'],
            'flat': updated_user['flat'],
            'phone': updated_user['phone'],
            'email': updated_user['email'],
            'designation': updated_user['designation'],
            'age': updated_user['age'],
            'gender': updated_user['gender'],
            'family_members': updated_user['family_members']
        }
        return jsonify({'user': user_data})
    else:
        return jsonify({'error': 'Update failed'}), 500

# ==================== COMPLAINTS ====================

@app.route('/api/complaints', methods=['GET'])
def list_complaints():
    user_id = request.args.get('user_id', type=int)
    if user_id:
        complaints = get_complaints(user_id=user_id)
    else:
        complaints = get_complaints()
    return jsonify([dict(c) for c in complaints])

@app.route('/api/complaints', methods=['POST'])
def add_complaint():
    # Expect multipart form data with file upload
    title = request.form.get('title')
    description = request.form.get('description')
    user_id = request.form.get('user_id', type=int)

    if not title or not description or not user_id:
        return jsonify({'error': 'Missing required fields'}), 400

    photo_path = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid collisions
            import time
            filename = f"{int(time.time())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_path = filename

    complaint_id = create_complaint(user_id, title, description, photo_path)
    return jsonify({'id': complaint_id}), 201

@app.route('/api/complaints/<int:complaint_id>/status', methods=['PUT'])
def update_complaint_status_route(complaint_id):
    data = request.get_json()
    status = data.get('status')
    if not status or status not in ['pending', 'in_progress', 'resolved']:
        return jsonify({'error': 'Invalid status'}), 400
    update_complaint_status(complaint_id, status)
    return jsonify({'success': True})

# ==================== ADMIN: USER MANAGEMENT ====================

@app.route('/api/admin/users', methods=['GET'])
def list_users():
    # In a real app, you'd check admin role via token/session
    users = get_all_users()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    delete_user(user_id)
    return jsonify({'success': True})

# ==================== UPLOADS (serve images) ====================
@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== SOS ====================
@app.route('/api/sos', methods=['POST'])
def sos_alert():
    data = request.get_json()
    user_id = data.get('user_id')
    location = data.get('location', '')
    with get_db() as conn:
        conn.execute('''
            INSERT INTO sos_logs (user_id, location, notified)
            VALUES (?, ?, ?)
        ''', (user_id, location, 'security@urbanbyte.com, guard_phone'))
        conn.commit()
    return jsonify({'success': True})

# ==================== VISITOR MANAGEMENT ====================
@app.route('/api/visitors', methods=['GET'])
def list_visitors():
    with get_db() as conn:
        visitors = conn.execute('SELECT * FROM visitors ORDER BY created_at DESC').fetchall()
        return jsonify([dict(v) for v in visitors])

@app.route('/api/visitors', methods=['POST'])
def add_visitor():
    data = request.get_json()
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO visitors (visitor_name, flat, purpose)
            VALUES (?, ?, ?)
        ''', (data['visitor_name'], data['flat'], data.get('purpose')))
        conn.commit()
        return jsonify({'id': cursor.lastrowid}), 201

@app.route('/api/visitors/<int:visitor_id>/status', methods=['PUT'])
def update_visitor_status(visitor_id):
    data = request.get_json()
    status = data.get('status')
    with get_db() as conn:
        if status == 'approved':
            conn.execute('UPDATE visitors SET status = ? WHERE id = ?', (status, visitor_id))
        elif status == 'checked_in':
            conn.execute('UPDATE visitors SET status = ?, check_in_time = CURRENT_TIMESTAMP WHERE id = ?', (status, visitor_id))
        elif status == 'checked_out':
            conn.execute('UPDATE visitors SET status = ?, check_out_time = CURRENT_TIMESTAMP WHERE id = ?', (status, visitor_id))
        else:
            return jsonify({'error': 'Invalid status'}), 400
        conn.commit()
        return jsonify({'success': True})

# ==================== POLLS ====================
@app.route('/api/polls', methods=['GET'])
def list_polls():
    with get_db() as conn:
        polls = conn.execute('SELECT * FROM polls ORDER BY created_at DESC').fetchall()
        return jsonify([dict(p) for p in polls])

@app.route('/api/polls', methods=['POST'])
def create_poll():
    data = request.get_json()
    options_json = json.dumps(data['options'])
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO polls (title, options, created_by)
            VALUES (?, ?, ?)
        ''', (data['title'], options_json, data['created_by']))
        conn.commit()
        return jsonify({'id': cursor.lastrowid}), 201

@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
def vote_poll(poll_id):
    data = request.get_json()
    user_id = data.get('user_id')
    option_index = data.get('option_index')
    if user_id is None or option_index is None:
        return jsonify({'error': 'Missing user_id or option_index'}), 400
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO votes (poll_id, user_id, option_index)
                VALUES (?, ?, ?)
            ''', (poll_id, user_id, option_index))
            conn.commit()
            return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already voted'}), 409

@app.route('/api/polls/<int:poll_id>/results', methods=['GET'])
def poll_results(poll_id):
    with get_db() as conn:
        poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
        if not poll:
            return jsonify({'error': 'Poll not found'}), 404
        options = json.loads(poll['options'])
        votes = conn.execute('SELECT option_index, COUNT(*) as count FROM votes WHERE poll_id = ? GROUP BY option_index', (poll_id,)).fetchall()
        counts = [0] * len(options)
        for v in votes:
            counts[v['option_index']] = v['count']
        return jsonify({'options': options, 'votes': counts})

if __name__ == '__main__':
    app.run(debug=True)