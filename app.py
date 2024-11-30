from flask import *
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage 
from email.mime.multipart import MIMEMultipart 
import smtplib 

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

def automatedEmail(issue, username):
    msg = MIMEMultipart()
    msg['Subject'] = "Response to issue."

    text = f'''
<html>
<body>
    <p>Dear <b>{username}</b>,</p>
    <p>We have received your inquiry regarding the following issue:</p>
    <p><i>"{issue}"</i></p>
    <p>
        Our staff will contact you within <b>1-3 business days</b> 
        to assist you with your issue.
    </p>
    <p>
        Thank you for being patient while we address this matter!
    </p>
    <p>
        Regards,<br>
        <b><i>SkyLink Co.</i><b>
    </p>
</body>
</html>
'''
    msg.attach(MIMEText(text, "html"))

    image_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if image_path and os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), name=os.path.basename(image_path))
            msg.attach(img)

    return msg

@app.route('/')
def home():
    if "user" in session and session["user"] != "":
        return render_template("index.html", profile_Name = session["user"])
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
            test_email = new_email.split("@")
            valid_emails = ['gmail.com', 'yahoo.com', 'hotmail.com', 'mmu.edu.my', 'live.com'] # Only these for now
            if (len(test_email) == 1) or test_email[1] not in valid_emails:
                flash("Invalid email!")
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

@app.route('/support', methods=["GET", "POST"])
def support():
    if "user" in session and session["user"] != "":
        if request.method == "POST":
            name = users.query.filter_by(username=session["user"]).first().username
            email = users.query.filter_by(username=session["user"]).first().email
            message = request.form.get("message")

            try:
                msg = automatedEmail(message, name)
                to = [email]
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                smtp_user = os.getenv("EMAIL_USER")  # Use environment variables
                smtp_password = os.getenv("EMAIL_PASSWORD")

                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                    smtp.sendmail(from_addr=smtp_user, to_addrs=to, msg=msg.as_string())

                flash(f"Your inquiry has been submitted successfully. Check your email ({email}) for our response!", "success")
            except Exception as e:
                flash(f"An error occurred while sending the email: {str(e)}", "danger")

            return redirect(url_for("support"))

        return render_template("support.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
