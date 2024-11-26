from flask import *
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime

load_dotenv('.env')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skylink.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv('APP_SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=30)

db = SQLAlchemy(app)

class users(db.Model):
    id = db.Column("id", db.Integer, primary_key = True, nullable = False, unique=True)
    icNumber = db.Column("icNumber", db.String(12), nullable = False, unique=True)
    name = db.Column("name", db.String(255), nullable = False)
    phoneNumber = db.Column("phoneNumber", db.String(15), nullable=False, unique=True) # The International Telecommunication Union's (ITU) E.164 standard recommends that phone numbers be no longer than 15 digits
    email = db.Column("email", db.String(100), nullable=False, unique=True) # we do check to find valid email by splitting end domain
    username = db.Column("username", db.String(20), nullable=False, unique=True)
    password = db.Column("password", db.String(18), nullable=False)

    def __init__(self, icNumber, name, phoneNumber, email, username, password):
        self.icNumber = icNumber
        self.name = name
        self.phoneNumber = phoneNumber
        self.email = email
        self.username = username
        self.password = password

@app.route('/')
def home():
    if "user" in session and session["user"] != "":
        return render_template("index.html")
    else:
        return redirect(url_for("register"))

@app.route('/home')
def redirectToDefault():
    return redirect(url_for("home"))

@app.route('/register', methods = ["POST", "GET"])
def register():
    if "user" in session and session["user"] != "":
        return redirect(url_for("home"))
    if request.method == "POST":
        new_ic = request.form["reg-ic"]
        new_name = request.form["reg-full-name"]
        new_hpNo = request.form["reg-hp-no"]
        new_email = request.form["reg-email"]
        new_username = request.form["reg-username"]
        new_password = request.form["reg-password"]
        
        if users.query.filter_by(icNumber = new_ic).first():
            flash(f"User with IC number {new_ic} already exists!")
        if users.query.filter_by(email = new_email).first() or users.query.filter_by(username = new_username).first():
            flash("Email or Username already exists!")
        if users.query.filter_by(phoneNumber = new_hpNo).first():
            flash("That phone number is already registered!")
        else:
            email_domain = ''.join(new_email.split("@")[1])
            valid_emails = ['gmail.com', 'yahoo.com', 'hotmail.com', 'mmu.edu.my', 'live.com'] # Only these for now
            if email_domain not in valid_emails:
                flash("Invalid email!")
            else:
                isCode = new_hpNo[0]
                if isCode == "+":
                    new_user = users(icNumber=new_ic, name=new_name, phoneNumber=new_hpNo, email=new_email, username=new_username, password=new_password)
                    db.session.add(new_user)
                    db.session.commit()   
                    return redirect(url_for("login"))
                else:
                    flash("Please include country calling code!")
    return render_template("register.html")

@app.route('/login', methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        usernameInput = request.form["login-username"]
        passwordInput = request.form["login-password"]

        if users.query.filter_by(username = usernameInput).first() and users.query.filter_by(username = usernameInput).first().password == passwordInput:
            session.permanent = True
            session["user"] = usernameInput
            return redirect(url_for("home"))
        else:
            flash("Invalid Username or Password!")
    return render_template("login.html")

@app.route('/logout')
def logout():
    if "user" in session and session["user"] != "":
        session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
