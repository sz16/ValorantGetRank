from flask import Flask, send_file, jsonify, Response
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Alive"

@app.route('/logs')
def send_logs():
    log_path = 'log.json'
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            data = f.read()
        # Trả về raw content kiểu JSON
        return Response(data, mimetype='application/json')
    else:
        return jsonify({"error": "Log file not found"}), 404

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
