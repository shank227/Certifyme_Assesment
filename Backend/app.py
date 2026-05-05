print("🔥 APP FILE EXECUTING")
import os
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
CORS(app, supports_credentials=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SECRET_KEY'] = 'secret123'

db = SQLAlchemy(app)

# ===== MODELS =====
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    reset_token = db.Column(db.String(200))
    reset_token_expiry = db.Column(db.DateTime)


# 🔥 NEW MODEL
class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    start_date = db.Column(db.String(50))
    description = db.Column(db.Text)
    skills = db.Column(db.String(200))
    future_opportunities = db.Column(db.String(200))
    max_applicants = db.Column(db.Integer)

    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))


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

    user = Admin(
        full_name=full_name,
        email=email,
        password=generate_password_hash(password, method='pbkdf2:sha256')
    )

    db.session.add(user)
    db.session.commit()

    return {"message": "Signup successful"}


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
        print("LOGIN USER ID:", user.id)  # 🔥 HERE
        session['admin_id'] = user.id

        if remember:
            session.permanent = True

        return {"message": "Login successful"}

    return {"error": "Invalid credentials"}, 401


# ✅ FORGOT PASSWORD
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


# 🔥 CREATE OPPORTUNITY
@app.route('/api/opportunities', methods=['POST'])
def create_opportunity():
    data = request.get_json()

    if 'admin_id' not in session:
        return {"error": "Unauthorized"}, 401

    print("CREATE → admin_id:", session.get('admin_id'))

    opportunity = Opportunity(
        name=data.get('name'),
        category=data.get('category'),
        duration=data.get('duration'),
        start_date=data.get('start_date'),
        description=data.get('description'),
        skills=data.get('skills'),
        future_opportunities=data.get('future_opportunities'),
        max_applicants=data.get('max_applicants'),
        admin_id=session['admin_id']
    )

    db.session.add(opportunity)

    print("BEFORE SAVE:", data)
    print("ADMIN ID BEING USED:", session.get('admin_id'))

    db.session.commit()

    # 🔥 ADD THIS
    all_opps = Opportunity.query.all()
    print("ALL OPPORTUNITIES IN DB:", all_opps)

    return {"message": "Opportunity created successfully"}

# 🔥 GET OPPORTUNITY
@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    if 'admin_id' not in session:
        return {"error": "Unauthorized"}, 401

    print("FETCH → admin_id:", session.get('admin_id'))

    # 🔥 Check EVERYTHING in DB
    all_opps = Opportunity.query.all()
    print("ALL OPPORTUNITIES IN DB:", all_opps)

    # 🔥 Check filtered result
    opportunities = Opportunity.query.filter_by(admin_id=session['admin_id']).all()
    print("FILTERED OPPORTUNITIES:", opportunities)

    result = []
    for opp in opportunities:
        result.append({
            "id": opp.id,
            "name": opp.name,
            "category": opp.category,
            "duration": opp.duration,
            "start_date": opp.start_date,
            "description": opp.description,
            "skills": opp.skills,
            "future_opportunities": opp.future_opportunities,
            "max_applicants": opp.max_applicants
        })

    return {"opportunities": result}

@app.route('/api/opportunities/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_opportunity(id):
    if request.method == 'OPTIONS':
        return {}, 200

    if 'admin_id' not in session:
        return {"error": "Unauthorized"}, 401

    opp = Opportunity.query.filter_by(
        id=id,
        admin_id=session['admin_id']
    ).first()

    if not opp:
        return {"error": "Not found"}, 404

    db.session.delete(opp)
    db.session.commit()

    return {"message": "Deleted"}

# ===== RUN APP =====
if __name__ == '__main__':
    print("🔥 ENTERED MAIN BLOCK")
    with app.app_context():
        print("🔥 CREATING DATABASE")
        db.create_all()
    print("🔥 STARTING FLASK SERVER")
    app.run(debug=True, use_reloader=False)