import os
import sys
import secrets
import sqlite3
import threading

from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# ✅ IMPORT WS
from server import start_ws_server, stop_ws_server

load_dotenv()

# --- Import SSO Middleware ---
sys.path.insert(0, os.path.dirname(__file__))
try:
    from shared_modules.sso_middleware import SSOMiddleware, WhitelistManager, RateLimiter, render_sso_error
except ImportError:
    from sso_middleware import SSOMiddleware, WhitelistManager, RateLimiter, render_sso_error

# ============================================================
# CONFIGURAZIONE APP
# ============================================================

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.secret_key = os.getenv('SERVER_SECRET_KEY', 'dev-secret-change-in-production')
app.permanent_session_lifetime = timedelta(hours=8)

SSO_MODE = os.getenv('SSO_MODE', 'production').lower()
DEV_USER_EMAIL = os.getenv('DEV_USER_EMAIL', 'demo@example.com')

SSO_CONFIG = {
    'jwt_secret': os.getenv('JWT_SECRET'),
    'jwt_algorithm': 'HS256',
    'jwt_issuer': 'sso-portal',
    'jwt_audience': os.getenv('APP_AUDIENCE', 'blueprint-app'),
    'session_timeout': 28800,
    'portal_url': os.getenv('PORTAL_URL', 'http://localhost:5000')
}

if SSO_MODE == 'production' and not SSO_CONFIG['jwt_secret']:
    raise ValueError("JWT_SECRET non configurato!")

if SSO_MODE == 'production':
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

# ============================================================
# DIRECTORY & PREFS
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PREFS_DIR = os.path.join(DATA_DIR, 'prefs')
os.makedirs(PREFS_DIR, exist_ok=True)

PREFS_DEFAULTS = {
    'theme': 'light',
    'notifications': 'on'
}

# ============================================================
# WHITELIST & RATE LIMITER
# ============================================================

whitelist_manager = WhitelistManager(
    whitelist_path=os.path.join(DATA_DIR, 'whitelist.json')
)

rate_limiter = RateLimiter(
    max_sessions_per_user=int(os.getenv('MAX_SESSIONS_PER_USER', 3)),
    max_sessions_global=int(os.getenv('MAX_SESSIONS_GLOBAL', 100)),
    session_ttl_seconds=28800
)

# ============================================================
# SSO MIDDLEWARE
# ============================================================

sso_middleware = SSOMiddleware(
    **SSO_CONFIG,
    whitelist_manager=whitelist_manager,
    rate_limiter=rate_limiter
)

# ============================================================
# DATABASE
# ============================================================

DB_PATH = os.path.join(DATA_DIR, 'scores.db')

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON scores(user_email)')
    conn.commit()
    conn.close()

def save_score(user_email: str, score: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO scores (user_email, score, timestamp) VALUES (?, ?, ?)',
        (user_email, score, datetime.utcnow().isoformat() + "Z")
    )
    conn.commit()
    conn.close()

def get_user_scores(email: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT score, timestamp FROM scores WHERE user_email=? ORDER BY timestamp DESC',
        (email,)
    )
    results = cursor.fetchall()
    conn.close()
    return [{'score': row[0], 'timestamp': row[1]} for row in results]

init_db()

# ============================================================
# WEBSOCKET CONTROL
# ============================================================

ws_started = False

@app.route('/start-ws')
@sso_middleware.sso_login_required
def start_ws():
    global ws_started

    if not ws_started:
        threading.Thread(target=start_ws_server, daemon=True).start()
        ws_started = True
        return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket</title>
        <style>
            body {
                background-color: #0f172a;
                color: white;
                font-family: Arial;
                text-align: center;
                padding-top: 100px;
            }
            .box {
                background: #1e293b;
                padding: 40px;
                border-radius: 15px;
                display: inline-block;
                box-shadow: 0 0 20px rgba(0,0,0,0.5);
            }
            a {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: #22c55e;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>🟢 WebSocket Avviato</h1>
            <p>Il server è attivo e pronto</p>
            <a href="/stop-ws">Ferma WebSocket</a>
        </div>
    </body>
    </html>
    """

    return  """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket</title>
    <style>
        body {
            background-color: #0f172a;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 100px;
        }
        .box {
            background: #1e293b;
            padding: 40px;
            border-radius: 15px;
            display: inline-block;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #eab308;
            color: black;
            text-decoration: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>🟡 WebSocket già attivo</h1>
        <p>Il server è già in esecuzione</p>
        <a href="/stop-ws">Ferma WebSocket</a>
    </div>
</body>
</html>
"""

@app.route('/stop-ws')
@sso_middleware.sso_login_required
def stop_ws():
    global ws_started

    if ws_started:
        stop_ws_server()
        ws_started = False
        return """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket</title>
    <style>
        body {
            background-color: #0f172a;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 100px;
        }
        .box {
            background: #1e293b;
            padding: 40px;
            border-radius: 15px;
            display: inline-block;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #ef4444;
            color: white;
            text-decoration: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>🔴 WebSocket Fermato</h1>
        <p>Il server è stato arrestato</p>
        <a href="/">Torna alla Home</a>
    </div>
</body>
</html>
"""

    return """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket</title>
    <style>
        body {
            background-color: #0f172a;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 100px;
        }
        .box {
            background: #1e293b;
            padding: 40px;
            border-radius: 15px;
            display: inline-block;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #22c55e;
            color: white;
            text-decoration: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>⚫ WebSocket già fermo</h1>
        <p>Il server non è attivo</p>
        <a href="/start-ws">Avvia WebSocket</a>
    </div>
</body>
</html>
"""


# ============================================================
# SSO LOGIN
# ============================================================

@app.route('/sso/login')
def sso_login():
    token = request.args.get('token')

    if SSO_MODE == 'dev' and not token and request.remote_addr == '127.0.0.1':
        dev_email = request.args.get('email') or DEV_USER_EMAIL
        user_data = {
            'email': dev_email,
            'name': get_username(dev_email).replace('.', ' ').title(),
            'googleId': 'dev-user-id',
            'picture': ''
        }
        return _complete_login(user_data)

    if not token:
        return render_sso_error("Token SSO mancante.", SSO_CONFIG['portal_url'])

    try:
        user_data = sso_middleware.validate_jwt(token)
        return _complete_login(user_data)
    except Exception:
        return render_sso_error("Token SSO non valido o scaduto.", SSO_CONFIG['portal_url'])

def _complete_login(user_data: dict):
    email = user_data.get('email', '')

    session.clear()
    session_id = secrets.token_hex(32)

    allowed, reason = rate_limiter.register_session(session_id, email)
    if not allowed:
        return render_sso_error(reason, SSO_CONFIG['portal_url'], status_code=429)

    sso_middleware.create_session(user_data, session, session_id=session_id)

    return redirect(url_for('home'))

# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    sid = session.get('session_id')
    if sid:
        rate_limiter.remove_session(sid)
    session.clear()
    return redirect(SSO_CONFIG['portal_url'])

# ============================================================
# API
# ============================================================

@app.route('/api/score', methods=['POST'])
@sso_middleware.sso_login_required
def receive_score():

    if request.headers.get("Content-Type") != "application/json":
        return jsonify({'error': 'Formato non valido'}), 400

    data = request.json

    try:
        score = int(data.get('score'))
        if score < 0 or score > 1000000:
            raise ValueError()
    except:
        return jsonify({'error': 'Score non valido'}), 400

    user_email = session['user']['email']
    save_score(user_email, score)

    return jsonify({'message': f'Score {score} salvato'})

@app.route('/api/scores')
@sso_middleware.sso_login_required
def scores():
    return jsonify(get_user_scores(session['user']['email']))

# ============================================================
# UTILITY
# ============================================================

def get_username(email: str) -> str:
    return email.split('@')[0]

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    user = session.get('user')
    user_scores = get_user_scores(user['email']) if user else []
    return render_template("home.html", user=user, user_scores=user_scores)

@app.route('/ciao')
def ciao():
    return "Ciao!"

@app.route('/mao')
@sso_middleware.sso_login_required
def mao():
    return session['user']['email']

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=3020)