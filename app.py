from flask import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skylink.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class users(db.Model):
    id = db.Column("id", db.Integer, pirmary_key = True, nullable = False)
    icNumber = db.Column("icNumber", db.String(12), nullable = False)
    name = db.Column("name", db.String(255), nullable = False)
    phoneNumber = db.Column("phoneNumber", db.String(15), nullable=False) # The International Telecommunication Union's (ITU) E.164 standard recommends that phone numbers be no longer than 15 digits
    email = db.Column("email", db.String(100), nullable=False) # we do check to find valid email by splitting end domain
    username = db.Column("username", db.String(20), nullable=False)
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
    return render_template("index.html")

@app.route('/home')
def redirectToDefault():
    return redirect(url_for("home"))

@app.route('/register', methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        new_ic = request.form["reg-ic"]
        new_name = request.form["reg-full-name"]
        new_hpNo = request.form["reg-hp-no"]
        new_email = request.form["reg-email"]
        new_username = request.form["reg-username"]
        new_password = request.form["reg-password"]
        
        if users.query.filter_by(email = new_email).first() or users.query.filter_by(username = new_username).first():
            flash("Email or Username already exists!")
        else:
            new_user = users(icNumber=new_ic, name=new_name, phoneNumber=new_hpNo, email=new_email, username=new_username, password=new_password)
            db.session.add(new_user)
            db.session.commit()   
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login')
def login():
    return render_template("login.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)