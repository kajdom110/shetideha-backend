from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import hmac
import re

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
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return 'سلام! این نسخه‌ی به‌روزرسانی‌شده‌ی بک‌اند است.'

@app.route('/api/services')
def services():
    services_list = [
        {'name': 'شت اول', 'description': 'توضیح خدمت اول'},
        {'name': 'شت دوم', 'description': 'توضیح خدمت دوم'},
        {'name': 'شت سوم', 'description': 'توضیح خدمت سوم'}
    ]
    return jsonify(services_list)

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
