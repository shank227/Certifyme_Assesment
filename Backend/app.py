print("🔥 APP FILE EXECUTING")


from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


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

# ===== ROUTES =====

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    email = data.get('email')
    full_name = data.get('full_name')
    password = data.get('password')

    print("DATA RECEIVED:", data)  # DEBUG LINE

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

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return {"error": "Missing credentials"}, 400

    user = Admin.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session['admin_id'] = user.id
        return {"message": "Login successful"}

    return {"error": "Invalid credentials"}, 401

if __name__ == '__main__':
    print("🔥 ENTERED MAIN BLOCK")
    with app.app_context():
        print("🔥 CREATING DATABASE")
        db.create_all()
    print("🔥 STARTING FLASK SERVER")
    app.run(debug=True, use_reloader=False)