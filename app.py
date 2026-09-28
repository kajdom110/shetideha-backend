from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
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

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

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
    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM messages').fetchall()
    conn.close()
    messages = [dict(row) for row in rows]
    return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True)
