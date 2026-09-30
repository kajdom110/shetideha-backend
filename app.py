from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import hmac
import re
from werkzeug.security import check_password_hash

app = Flask(__name__)

# something@something.something, with no spaces
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
CORS(app)

def init_db():
    conn = sqlite3.connect('messages.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
    ''')

    # Seed the services that used to be hard-coded, only if the table is empty
    count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    if count == 0:
        conn.executemany(
            'INSERT INTO services (title, description) VALUES (?, ?)',
            [
                ('شت اول', 'توضیح خدمت اول'),
                ('شت دوم', 'توضیح خدمت دوم'),
                ('شت سوم', 'توضیح خدمت سوم')
            ]
        )

    conn.commit()
    conn.close()

init_db()

def is_admin():
    admin_token = os.environ.get('ADMIN_TOKEN')
    sent_token = request.headers.get('X-Admin-Token')
    # If ADMIN_TOKEN isn't set, deny everyone instead of letting a missing header match it
    return bool(admin_token and sent_token and hmac.compare_digest(sent_token, admin_token))

@app.route('/')
def home():
    return 'سلام! این نسخه‌ی به‌روزرسانی‌شده‌ی بک‌اند است.'

@app.route('/api/services')
def services():
    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    services_list = [dict(row) for row in rows]
    return jsonify(services_list)

@app.route('/api/services', methods=['POST'])
def add_service():
    if not is_admin():
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'داده‌ی ارسالی معتبر نیست.'}), 400

    title = data.get('title')
    description = data.get('description')

    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'عنوان نباید خالی باشد.'}), 400
    if not isinstance(description, str) or not description.strip():
        return jsonify({'error': 'توضیحات نباید خالی باشد.'}), 400

    title = title.strip()
    description = description.strip()

    conn = sqlite3.connect('messages.db')
    cursor = conn.execute(
        'INSERT INTO services (title, description) VALUES (?, ?)',
        (title, description)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'id': new_id, 'title': title, 'description': description}), 201

@app.route('/api/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    if not is_admin():
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'داده‌ی ارسالی معتبر نیست.'}), 400

    title = data.get('title')
    description = data.get('description')

    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'عنوان نباید خالی باشد.'}), 400
    if not isinstance(description, str) or not description.strip():
        return jsonify({'error': 'توضیحات نباید خالی باشد.'}), 400

    title = title.strip()
    description = description.strip()

    conn = sqlite3.connect('messages.db')
    cursor = conn.execute(
        'UPDATE services SET title = ?, description = ? WHERE id = ?',
        (title, description, service_id)
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated == 0:
        return jsonify({'error': 'خدمتی با این شناسه پیدا نشد.'}), 404

    return jsonify({'id': service_id, 'title': title, 'description': description})

@app.route('/api/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    if not is_admin():
        return jsonify({'error': 'unauthorized'}), 401

    conn = sqlite3.connect('messages.db')
    cursor = conn.execute('DELETE FROM services WHERE id = ?', (service_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({'error': 'خدمتی با این شناسه پیدا نشد.'}), 404

    return jsonify({'status': 'success', 'message': 'خدمت حذف شد.'})

@app.route('/api/about')
def about():
    return jsonify({'message': 'ما یک کسب‌وکار کوچک هستیم که با تمرکز بر کیفیت و رضایت مشتری، خدمات خود را ارائه می‌دهیم.'})

@app.route('/api/contact', methods=['POST'])
def contact():
    # silent=True: a missing or invalid JSON body becomes None instead of an error
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'داده‌ی ارسالی معتبر نیست.'}), 400

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'نام نباید خالی باشد.'}), 400
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email.strip()):
        return jsonify({'error': 'ایمیل معتبر نیست.'}), 400
    if not isinstance(message, str) or not message.strip():
        return jsonify({'error': 'پیام نباید خالی باشد.'}), 400

    name = name.strip()
    email = email.strip()
    message = message.strip()

    conn = sqlite3.connect('messages.db')
    conn.execute(
        'INSERT INTO messages (name, email, message) VALUES (?, ?, ?)',
        (name, email, message)
    )
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'پیام شما دریافت و ذخیره شد!'})

@app.route('/api/messages')
def get_messages():
    admin_token = os.environ.get('ADMIN_TOKEN')
    sent_token = request.headers.get('X-Admin-Token')

    # If ADMIN_TOKEN isn't set, deny everyone instead of letting a missing header match it
    if not admin_token or not sent_token or not hmac.compare_digest(sent_token, admin_token):
        return jsonify({'error': 'unauthorized'}), 401

    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM messages').fetchall()
    conn.close()
    messages = [dict(row) for row in rows]
    return jsonify(messages)

@app.route('/api/login', methods=['POST'])
def login():
    error = jsonify({'error': 'نام‌کاربری یا رمز اشتباه است.'}), 401

    admin_username = os.environ.get('ADMIN_USERNAME')
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
    admin_token = os.environ.get('ADMIN_TOKEN')

    # If any of these isn't set, deny everyone
    if not admin_username or not admin_password_hash or not admin_token:
        return error

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error

    username = data.get('username')
    password = data.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        return error

    # Compare as bytes so non-ASCII usernames work with compare_digest
    username_ok = hmac.compare_digest(username.encode(), admin_username.encode())
    password_ok = check_password_hash(admin_password_hash, password)
    if not (username_ok and password_ok):
        return error

    return jsonify({'token': admin_token})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
