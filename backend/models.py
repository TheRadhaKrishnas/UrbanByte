import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# Database connection context manager
@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize database tables
def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table with new profile fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('member', 'management')),
                member_code TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                flat TEXT,
                phone TEXT,
                email TEXT,
                designation TEXT,
                age INTEGER,
                gender TEXT,
                family_members INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN age INTEGER')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN gender TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN family_members INTEGER')
        except sqlite3.OperationalError:
            pass

        # Complaints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                photo_path TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'resolved')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # Visitors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_name TEXT NOT NULL,
                flat TEXT NOT NULL,
                purpose TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'checked_in', 'checked_out')),
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Polls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                options TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # Votes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                option_index INTEGER NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (poll_id) REFERENCES polls (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(poll_id, user_id)
            )
        ''')

        # SOS logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sos_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                location TEXT,
                notified TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # Insert default admin and member if not exists
        cursor.execute("SELECT * FROM users WHERE member_code = 'ADMIN'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (role, member_code, password, name, designation)
                VALUES (?, ?, ?, ?, ?)
            ''', ('management', 'ADMIN', generate_password_hash('admin'), 'Admin User', 'Administrator'))

        cursor.execute("SELECT * FROM users WHERE member_code = 'MEM123'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (role, member_code, password, name, flat, phone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('member', 'MEM123', generate_password_hash('pass'), 'Anant Vijay', 'A-101', '9876543210', 'anant@example.com'))

        conn.commit()

# Helper to get user by ID
def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

# Helper to get user by member_code
def get_user_by_code(member_code):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE member_code = ?', (member_code,)).fetchone()

# Helper to verify password
def verify_password(stored_password, plain_password):
    return check_password_hash(stored_password, plain_password)

# Helper to create new user
def create_user(user_data):
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO users (role, member_code, password, name, flat, phone, email, designation, age, gender, family_members)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data.get('role', 'member'),
            user_data['member_code'],
            generate_password_hash(user_data['password']),
            user_data['name'],
            user_data.get('flat'),
            user_data.get('phone'),
            user_data.get('email'),
            user_data.get('designation'),
            user_data.get('age'),
            user_data.get('gender'),
            user_data.get('family_members')
        ))
        conn.commit()
        return cursor.lastrowid

# Helper to update user
def update_user(user_id, update_data):
    with get_db() as conn:
        fields = []
        values = []
        allowed_fields = ['name', 'flat', 'phone', 'email', 'age', 'gender', 'family_members', 'designation']
        for field in allowed_fields:
            if field in update_data:
                fields.append(f"{field}=?")
                values.append(update_data[field])
        if not fields:
            return False
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id=?"
        conn.execute(query, values)
        conn.commit()
        return True

# Helper to get all complaints (optionally filtered by user_id)
def get_complaints(user_id=None):
    with get_db() as conn:
        if user_id:
            return conn.execute('''
                SELECT c.*, u.name as user_name FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
            ''', (user_id,)).fetchall()
        else:
            return conn.execute('''
                SELECT c.*, u.name as user_name FROM complaints c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
            ''').fetchall()

# Helper to create complaint
def create_complaint(user_id, title, description, photo_path):
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO complaints (user_id, title, description, photo_path)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, description, photo_path))
        conn.commit()
        return cursor.lastrowid

# Helper to update complaint status
def update_complaint_status(complaint_id, status):
    with get_db() as conn:
        conn.execute('UPDATE complaints SET status = ? WHERE id = ?', (status, complaint_id))
        conn.commit()
        return True

# Helper to get all users (for admin)
def get_all_users():
    with get_db() as conn:
        return conn.execute('SELECT id, role, member_code, name, flat, phone, email, designation, age, gender, family_members, created_at FROM users ORDER BY id').fetchall()

# Helper to delete user (admin)
def delete_user(user_id):
    with get_db() as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()