from flask import *
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage 
from email.mime.multipart import MIMEMultipart 
import smtplib 
import requests
import time
from flask_wtf.csrf import CSRFProtect

load_dotenv('.env')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skylink.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv('APP_SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=30)
csrf = CSRFProtect(app)

apiKey = os.getenv('AMADEUSAPIKEY')
apiSecret = os.getenv('AMADEUSAPISECRET')
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

token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token(client_id, client_secret):
    # Check if the cached token is still valid
    if token_cache["access_token"] and time.time() < token_cache["expires_at"]:
        return token_cache["access_token"]

    # Otherwise, fetch a new token
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        # Cache the token and its expiration time
        token_cache["access_token"] = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 0)  # Expiration time in seconds
        token_cache["expires_at"] = time.time() + expires_in - 60  # Refresh slightly before expiry
        return token_cache["access_token"]
    else:
        raise Exception(f"Failed to authenticate: {response.status_code}, {response.text}")

def get_flights(origin, destination, passengers, date, access_token):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": date,
        "adults": passengers,  
        "nonStop": "false",
        "max": 5
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch flights: {response.status_code}, {response.text}")

def extract_flight_details(flights_data):
    flight_details = []
    for offer in flights_data.get("data", []):
        # Extract price details
        price_details = offer.get("price", {})
        total_price = price_details.get("total")
        currency = price_details.get("currency")
        
        # Extract flight segments
        for segment in offer["itineraries"][0]["segments"]:
            flight_details.append({
                "flight_number": segment["carrierCode"] + segment["number"],
                "airline": segment["operating"]["carrierCode"],
                "departure_time": segment["departure"]["at"],
                "arrival_time": segment["arrival"]["at"],
                "price": f"{currency} {total_price}" if total_price and currency else "N/A"
            })
    return flight_details


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
        <b>SkyLink Co.<b>
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

access_token = get_access_token(apiKey, apiSecret)

@app.route('/', methods = ["POST", 'GET'])
def home():
    if "user" in session and session["user"] != "":
        # Read options from the .txt file
        try:
            with open('static/airport_lists.txt', 'r') as file:
                options = [line.strip() for line in file if line.strip()]  # Remove empty lines
        except FileNotFoundError:
            options = []
        if request.method == "POST":
                selected_trip = request.form.get('trip')
                if selected_trip == "round-trip":
                    return_date = request.form.get('return-date')
                else:
                    return_date = "None"
                passengers = request.form.get('number-of-passengers')
                promo_code = request.form.get('promo-code')
                stops = []
                for key in request.form:
                    if key.startswith('origin-location') or key.startswith('destination-location'):
                        stops.append({key: request.form[key]})
                departureDates = []
                for r in request.form:
                    if r.startswith('departure-date'):
                        departureDates.append({r: request.form[r]})
                originLocations = ",".join(value for stop in stops for key, value in stop.items() if key.startswith('origin-location'))
                destinationLocations = ",".join(value2 for stop2 in stops for key2, value2 in stop2.items() if key2.startswith('destination-location'))
                departures = ",".join(value3 for date in departureDates for key3, value3 in date.items() if key3.startswith('departure-date'))
                return redirect(url_for(
                    "flights",
                    trip=selected_trip,
                    return_date=return_date,
                    passengers=passengers,
                    promo_code=promo_code,
                    origin_locations=originLocations,
                    destination_locations=destinationLocations,
                    departure_dates=departures
                ))
        return render_template("index.html", profile_Name = session["user"], options=options)
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
        try:
            int(new_ic)
            if users.query.filter_by(icNumber = str(new_ic)).first():
                flash(f"User with IC number {new_ic} already exists!")
            if users.query.filter_by(email = new_email).first() or users.query.filter_by(username = new_username).first():
                flash("Email or Username already exists!")
            if users.query.filter_by(phoneNumber = new_hpNo).first():
                flash("That phone number is already registered!")
            else:
                test_email = new_email.split("@")
                valid_emails = ['gmail.com', 'yahoo.com', 'hotmail.com', 'mmu.edu.my', 'live.com', 'student.mmu.edu.my'] # Only these for now
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
        except:
            flash("Please enter a valid IC Number.")
        
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

        return render_template("support.html", profile_Name = session["user"])
@app.route('/check-in', methods=["GET", "POST"])
def check_in():
    if request.method == "POST":
        ic_number = request.form.get("ic_number") 
        email = request.form.get("email")


        user = users.query.filter_by(icNumber=ic_number, email=email).first()

        if user:

            flash(f"Check-in successful! Welcome, {user.name}.", "success")
            return redirect(url_for("check_in"))
        else:

            flash("Invalid IC Number or Email. Please try again.", "error")
            return redirect(url_for("check_in"))


    return render_template("check_in.html")

@app.route('/flights')
def flights():
    trip = request.args.get('trip')
    return_date = request.args.get('return_date')
    passengers = request.args.get('passengers')
    promo_code = request.args.get('promo_code')
    origin_locations = request.args.get('origin_locations')
    destination_locations = request.args.get('destination_locations')
    departure_dates = request.args.get('departure_dates')
    if trip == "one-way":
        try:
            origin_location = (origin_locations.split(",")[0])
            originCode = origin_location[-4:-1]
            destination_location = (destination_locations.split(",")[0])
            destinationCode = destination_location[-4:-1]
            departure_date = departure_dates.split(",")[0]
            date_object = datetime.strptime(departure_date, "%Y-%m-%d")
            day = date_object.strftime("%A")
            passengerNum = int(passengers[0])
            print(origin_location)
            # flights = get_flights(origin_location, destination_location, passengerNum, departure_date, access_token)
            # flight_details = extract_flight_details(flights)
            # priceList = []
            # departureTimeList = []
            # arrivalTimeList = []
            # flightNumList = []
            # airlineList = []

            # for flight in flight_details:
            #     print(f"Flight: {flight['flight_number']}, Airline: {flight['airline']}, "
            #     f"Departure: {flight['departure_time']}, Arrival: {flight['arrival_time']}, Price: {flight['price']}")
            #     flightNumList.append(flight['flight_number'])
            #     airlineList.append(flight['airline'])
            #     departureTimeList.append(flight['departure_time'])
            #     arrivalTimeList.append(flight['arrival_time'])
            #     priceList.append(flight['price'])
            # priceList.sort()
            return render_template(
                "flights.html",
                profile_Name = session["user"], 
                origin_location=origin_location, 
                destination_location=destination_location, 
                day=day, 
                departure_date=departure_date, 
                passengerNum=passengerNum
            )
        except Exception as e:
            print(f"Error: {e}")
    return render_template("flights.html", profile_Name = session["user"])

@app.route('/profile')
def profile():
    return render_template("profile.html", profile_Name = session["user"])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
