from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import hashlib
import bcrypt
from datetime import datetime, timedelta
import os
import io
import random
import os as _os
def _mysql_password():
    pwd = _os.environ.get("MYSQL_ROOT_PASSWORD", "")
    if pwd:
        return pwd
    try:
        with open(_os.path.expanduser("~/.my.cnf")) as f:
            for line in f:
                if line.startswith("password="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


app = Flask(__name__)

@app.route('/api/health')
def health_check(): return {"status": "online", "uptime": "99.9%"}

@app.route('/api/version')
def version_check(): return {"version": "2.0.4-Imperial"}

@app.route('/api/system/status')
def system_status(): return {"cpu": "12%", "memory": "45%", "status": "stable"}

@app.route('/api/business/data')
def business_data(): return {"revenue": 94000000, "currency": "ZAR"}

@app.route('/create_payment')
def cp_route(): return render_template('create_payment.html', user=type('User', (), {'username': 'Humbulani'}))

@app.route('/create_order')
def co_route(): return render_template('create_order.html', user=type('User', (), {'username': 'Humbulani'}))

@app.route('/notification-settings')
def ns_route(): return render_template('notification_settings.html', user=type('User', (), {'username': 'Humbulani'}))

app.config['SECRET_KEY'] = 'imperial_secret_123'
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://root:{_mysql_password()}@localhost/imperial_nexus?unix_socket=/data/data/com.termux/files/home/mysql_run/mysql.sock"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def hash_password(password):
    # If checking an input string, return standard sha256 hex string
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(user, password_input):
    if not user:
        return False
    # If the stored password is a Bcrypt hash, verify with bcrypt
    if user.password.startswith(('$2a$', '$2b$', '$2y$')):
        return bcrypt.checkpw(password_input.encode(), user.password.encode())
    # Otherwise fallback to standard SHA-256 match
    return user.password == hash_password(password_input)

# ==================== MODELS ====================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")
    phone = db.Column(db.String(20), nullable=True)
    village = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class USSDSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.String(20))
    current_menu = db.Column(db.String(50), default='main')
    amount = db.Column(db.Float, default=0)
    recipient = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== WEB ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = hash_password(request.form['password'])
        new_user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=hashed,
            phone=request.form.get('phone', '')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password(user, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    payments = Payment.query.filter_by(user_id=current_user.id).all()
    
    # Calculate stats
    stats = {
        'my_orders': len(orders),
        'my_payments': len(payments),
        'total_spent': sum(p.amount for p in payments)
    }
    
    if current_user.role == 'admin':
        stats['total_users'] = User.query.count()
        stats['total_orders'] = Order.query.count()
        stats['total_payments'] = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    
    return render_template('dashboard.html', user=current_user, orders=orders, payments=payments, stats=stats)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==================== USER ACTIONS ====================
@app.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':
        order_no = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_order = Order(
            order_number=order_no,
            customer_id=current_user.id,
            description=request.form.get('description'),
            amount=float(request.form.get('amount', 0))
        )
        db.session.add(new_order)
        db.session.commit()
        flash('Order created successfully!')
        return redirect(url_for('dashboard'))
    return render_template('create_order.html')

@app.route('/create_payment', methods=['GET', 'POST'])
@login_required
def create_payment():
    if request.method == 'POST':
        pay_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_payment = Payment(
            payment_id=pay_id,
            user_id=current_user.id,
            amount=float(request.form.get('amount', 0)),
            payment_method=request.form.get('method')
        )
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment submitted!')
        return redirect(url_for('dashboard'))
    return render_template('create_payment.html')

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/my_payments')
@login_required
def my_payments():
    payments = Payment.query.filter_by(user_id=current_user.id).all()
    return render_template('my_payments.html', payments=payments)

# ==================== API ENDPOINTS ====================
@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/mobile/config')
def mobile_config():
    return jsonify({
        'app_name': 'Imperial Network',
        'version': '2.0.0',
        'api_base': 'http://10.69.206.69:8000/api',
        'features': {'orders': True, 'payments': True, 'ussd': True}
    })

@app.route('/api/mobile/login', methods=['POST'])
def mobile_login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if user and check_password(user, data.get('password')):
        return jsonify({
            'success': True,
            'user': {'id': user.id, 'username': user.username, 'role': user.role},
            'token': f'token-{user.id}-{datetime.utcnow().timestamp()}'
        })
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/stats')
@login_required
def api_stats():
    if current_user.role == 'admin':
        return jsonify({
            'total_users': User.query.count(),
            'total_orders': Order.query.count(),
            'total_revenue': db.session.query(db.func.sum(Payment.amount)).scalar() or 0
        })
    return jsonify({
        'my_orders': Order.query.filter_by(customer_id=current_user.id).count(),
        'my_payments': Payment.query.filter_by(user_id=current_user.id).count()
    })

# ==================== USSD SYSTEM ====================
@app.route('/ussd', methods=['GET', 'POST'])
def ussd_callback():
    session_id = request.values.get('sessionId', '')
    phone_number = request.values.get('phoneNumber', '')
    text = request.values.get('text', '')
    
    session = USSDSession.query.filter_by(session_id=session_id).first()
    if not session:
        session = USSDSession(session_id=session_id, phone_number=phone_number)
        db.session.add(session)
        db.session.commit()
    
    if text == '':
        response = "CON Welcome to Imperial\n1. Check Balance\n2. Send Money\n3. Buy Airtime"
    elif text == '1':
        response = f"END Your balance: R{random.randint(100, 500)}.00"
    elif text == '2':
        response = "CON Enter amount to send:"
    elif text.startswith('2*'):
        amount = text.split('*')[1]
        response = f"CON Confirm sending R{amount} to 0712345678?\n1. Confirm\n2. Cancel"
    elif text == '2*100*1':
        response = "END Transaction successful! Ref: TRX123"
    else:
        response = "END Thank you for using Imperial Network"
    
    return response

@app.route('/ussd/simulate', methods=['GET', 'POST'])
def ussd_simulate():
    result = None
    if request.method == 'POST':
        text = request.form.get('text', '')
        if text == '':
            result = "CON Welcome to Imperial\n1. Check Balance\n2. Send Money"
        elif text == '1':
            result = f"END Your balance: R{random.randint(100, 500)}.00"
        else:
            result = "END Transaction completed"
    return render_template('ussd_simulate.html', result=result)

@app.route('/ussd/admin')
@login_required
def ussd_admin():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    sessions = USSDSession.query.order_by(USSDSession.updated_at.desc()).limit(20).all()
    stats = {
        'total_sessions': USSDSession.query.count(),
        'active_sessions': USSDSession.query.filter(USSDSession.updated_at > datetime.utcnow() - timedelta(minutes=5)).count()
    }
    return render_template('ussd_admin.html', sessions=sessions, stats=stats)

# ==================== AI DASHBOARD ====================
@app.route('/ai/dashboard')
@login_required
def ai_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = User.query.filter(User.created_at > week_ago).count()
    
    trends = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_total = db.session.query(db.func.sum(Payment.amount)).filter(
            db.func.date(Payment.created_at) == day.date()
        ).scalar() or 0
        trends.append({'date': day.strftime('%Y-%m-%d'), 'amount': float(day_total)})
    
    health = {
        'system_health': '99.9%',
        'response_time': f'{random.randint(20, 40)}ms',
        'anomalies_detected': random.randint(0, 2),
        'active_services': 12,
        'total_services': 12,
        'stats': {
            'total_users': User.query.count(),
            'total_orders': Order.query.count(),
            'total_revenue': db.session.query(db.func.sum(Payment.amount)).scalar() or 0,
            'new_users_week': new_users
        },
        'predictions': {
            'next_hour': 'stable',
            'next_day': 'stable',
            'week_growth': f'+{new_users * 2} users',
            'revenue_forecast': f'R{random.randint(1000, 5000)}'
        },
        'trends': trends
    }
    return render_template(
        'ai_dashboard.html', 
        health=health, 
        stats={
            'active_users': health['stats']['total_users'],
            'total_orders': health['stats']['total_orders'],
            'total_revenue': health['stats']['total_revenue'],
            'new_users_week': health['stats']['new_users_week']
        },
        predictions={
            'revenue': random.randint(1000, 5000),
            'next_hour': health['predictions']['next_hour'],
            'next_day': health['predictions']['next_day']
        }
    )

# ==================== MOBILE SDK ====================
@app.route('/mobile')
@login_required
def mobile():
    return render_template('mobile.html')

@app.route('/mobile/sdk')
@login_required
def mobile_sdk():
    return render_template('mobile_sdk.html')

@app.route('/mobile/sdk/download')
@login_required
def mobile_sdk_download():
    # Create a simple SDK documentation file
    sdk_content = """
Imperial Mobile SDK v2.0.0
=========================
Base URL: http://10.69.206.69:8000

Endpoints:
- GET /api/mobile/config
- POST /api/mobile/login
- GET /api/stats

Flutter Integration:
--------------------
final response = await http.get('http://10.69.206.69:8000/api/mobile/config');
    """
    return send_file(
        io.BytesIO(sdk_content.encode()),
        mimetype='text/plain',
        as_attachment=True,
        download_name='imperial_sdk.txt'
    )


@app.route('/monitor')
@login_required
def monitor():
    return render_template('monitor.html')

@app.route('/api/version')
def get_version():
    return jsonify({'version': '2.0.0', 'status': 'stable'})

@app.route('/api/business/data')
def get_business_data():
    return jsonify({
        'status': 'active',
        'revenue_stream': 'imperial_core',
        'nodes_connected': 12
    })


@app.route('/api/system/status')
def api_system_status():
    return jsonify({
        'status': 'operational',
        'imperial_stack': 'active',
        'nodes': {
            'ai_node': '11434',
            'gateway': '8102',
            'apex': '8086'
        },
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/admin/keys')
@login_required
def admin_keys():
    return render_template('admin_keys.html')


@app.route('/api/status/full')
def api_status_full():
    return jsonify({
        'system': 'Imperial Network',
        'status': 'online',
        'database': 'connected',
        'ai_engine': 'running',
        'ussd_gateway': 'active',
        'api_version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)
