print("🔥 APP FILE EXECUTING")

from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret123'

db = SQLAlchemy(app)

# ===== MODELS =====
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    # 🔥 Forgot password fields
    reset_token = db.Column(db.String(200))
    reset_token_expiry = db.Column(db.DateTime)

# ===== ROUTES =====

# ✅ SIGNUP
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    email = data.get('email')
    full_name = data.get('full_name')
    password = data.get('password')

    if not email or not full_name or not password:
        return {"error": "All fields required"}, 400

    existing = Admin.query.filter_by(email=email).first()
    if existing:
        return {"error": "Email already exists"}, 400

    try:
        user = Admin(
            full_name=full_name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )

        db.session.add(user)
        db.session.commit()

        return {"message": "Signup successful"}

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": "Server error"}, 500


# ✅ LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    email = data.get('email')
    password = data.get('password')
    remember = data.get('remember')

    user = Admin.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session['admin_id'] = user.id

        if remember:
            session.permanent = True

        return {"message": "Login successful"}

    return {"error": "Invalid credentials"}, 401


# ✅ FORGOT PASSWORD (POSTMAN DEMO)
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    user = Admin.query.filter_by(email=email).first()
    print("USER FOUND:", user)

    if user:
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        print("RESET TOKEN:", token)

    return {"message": "If the email exists, a reset link has been generated"}


# ✅ RESET PASSWORD
@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()

    token = data.get('token')
    new_password = data.get('password')

    user = Admin.query.filter_by(reset_token=token).first()

    if not user:
        return {"error": "Invalid or expired token"}, 400

    if user.reset_token_expiry < datetime.utcnow():
        return {"error": "Token expired"}, 400

    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    user.reset_token = None
    user.reset_token_expiry = None

    db.session.commit()

    return {"message": "Password reset successful"}


# ===== RUN APP =====
if __name__ == '__main__':
    print("🔥 ENTERED MAIN BLOCK")
    with app.app_context():
        print("🔥 CREATING DATABASE")
        db.create_all()
    print("🔥 STARTING FLASK SERVER")
    app.run(debug=True, use_reloader=False)