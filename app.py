from flask import *
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime, date
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage 
from email.mime.multipart import MIMEMultipart 
import smtplib 
import requests
import time
from flask_wtf.csrf import CSRFProtect
import random
import threading

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
    two_factor_auth = db.Column("two_factor_auth", db.Integer, nullable=False, default=0)
    isAdmin = db.Column("isAdmin", db.Boolean, nullable=False)

    bookings = db.relationship('bookings', backref='user', lazy=True)
    supportlogs = db.relationship('supportlogs', backref='support_user', lazy=True)

    def __init__(self, icNumber, name, phoneNumber, email, username, password, two_factor_auth, isAdmin):
        self.icNumber = icNumber
        self.name = name
        self.phoneNumber = phoneNumber
        self.email = email
        self.username = username
        self.password = password
        self.two_factor_auth = two_factor_auth
        self.isAdmin = isAdmin

class bookings(db.Model):
    bookingNum = db.Column("bookingNum", db.String(5), primary_key=True, nullable=False, unique=True)
    firstName = db.Column("firstName", db.String(255), nullable=False, unique=False)
    surname = db.Column("surname", db.String(255), nullable=False, unique=False)
    icNum = db.Column("icNum", db.String(12), nullable=False, unique=False)
    phoneNum = db.Column("phoneNum", db.String(15), nullable=False, unique=False)
    origin = db.Column("origin", db.String(255), nullable=False, unique=False)
    destination = db.Column("destination", db.String(255), nullable=False, unique=False)
    departureTime = db.Column("departureTime", db.String(5), nullable=False)
    arrivalTime = db.Column("arrivalTime", db.String(5), nullable=False)
    date = db.Column("date", db.String(12), nullable=False)
    airline = db.Column("airline", db.String(20), nullable=False)
    flightNum = db.Column("flightNum", db.String(7), nullable=False)
    seatNum = db.Column("seatNum", db.String(4), nullable=False)
    isCheckedIn = db.Column("isCheckedIn", db.Boolean, nullable=False)

    bookingUserID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def _init_(self, bookingNum, firstName, surname, icNum, phoneNum, origin, destination, departureTime, arrivalTime, date, airline, flightNum, seatNum, isCheckedIn, bookingUserID):
        self.bookingNum = bookingNum
        self.firstName = firstName
        self.surname = surname
        self.icNum = icNum
        self.phoneNum = phoneNum
        self.origin = origin
        self.destination = destination
        self.departureTime = departureTime
        self.arrivalTime = arrivalTime
        self.date = date
        self.airline = airline
        self.flightNum = flightNum
        self.seatNum = seatNum
        self.isCheckedIn = isCheckedIn
        self.bookingUserID = bookingUserID

class supportlogs(db.Model):
    supportID = db.Column("supportID", db.Integer, primary_key=True, nullable=False, unique=True)
    supportRequest = db.Column("supportRequest", db.Text, nullable=False)
    supportDate = db.Column("supportDate", db.String(10), nullable=False)
    supportUser = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, supportRequest, supportDate, supportUser):
        self.supportRequest = supportRequest
        self.supportDate = supportDate
        self.supportUser = supportUser

CACHE_FILE = "token_cache.json"
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    else:
        with open(CACHE_FILE, "x") as file:
            json.dump({}, file)
        return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file)

token_cache = load_cache()

def get_access_token(client_id, client_secret):
    if "access_token" in token_cache and time.time() < token_cache.get("expires_at", 0):
        return token_cache["access_token"]
    
    print("Hi")
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
        token_cache["access_token"] = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 0)  # Time in seconds
        token_cache["expires_at"] = time.time() + expires_in - 60  # Refresh before expiry
        save_cache(token_cache)
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
        "max": "4"
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch flights: {response.status_code}, {response.text}")
        raise Exception(f"Failed to fetch flights: {response.status_code}, {response.text}")
    
def extract_flight_details(flights_data, max_results=5):
    flight_details = []
    for offer in flights_data.get("data", [])[:max_results]:  # Limit to max_results
        price_details = offer.get("price", {})
        total_price = price_details.get("total")
        for segment in offer["itineraries"][0]["segments"]:
            flight_details.append({
                "flight_number": segment["carrierCode"] + segment["number"],
                "airline": segment["operating"]["carrierCode"],
                "departure_time": segment["departure"]["at"],
                "arrival_time": segment["arrival"]["at"],
                "price": f"{round((float(total_price)*4.67), 2)}" if total_price else "N/A"
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
    msg.attach(MIMEText(text, "html", "utf-8"))

    image_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if image_path and os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), name=os.path.basename(image_path))
            msg.attach(img)

    return msg

@app.route('/', methods = ["POST", 'GET'])
def home():
    if "user" in session and session["user"] != "":
        email = users.query.filter_by(username = session["user"]).first().email
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
                if (('Sultan Haji Ahmad Shah Airport (KUA)' in destinationLocations.split(',') and promo_code=="KUANTAN20")  or ("Sultan Mahmud Airport (TGG)" in destinationLocations.split(',') and promo_code=="GANU10")) or (promo_code == ""):
                    if selected_trip != "multi-city":
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
                    else:
                        return redirect(url_for(
                            "flightsmulticity",
                            trip=selected_trip,
                            passengers=passengers,
                            promo_code=promo_code,
                            origin_locations=originLocations,
                            destination_locations=destinationLocations,
                            departure_dates=departures
                        ))
                else:
                    if promo_code == "KUANTAN20" or promo_code == "GANU10":
                        flash("Promo Code cannot be used for this destination!")
                        return redirect(url_for("home"))
                    else:
                        flash("Invalid Promo Code")
                        return redirect(url_for("home"))
        return render_template("index.html", profile_Name = session["user"], options=options, email=email)
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
                    if new_email == "skylinkcustomerservice@gmail.com":
                        new_user = users(icNumber=new_ic, name=new_name, phoneNumber=new_hpNo, email=new_email, username=new_username, password=new_password, two_factor_auth=0, isAdmin=True)
                    else:
                        new_user = users(icNumber=new_ic, name=new_name, phoneNumber=new_hpNo, email=new_email, username=new_username, password=new_password, two_factor_auth=0, isAdmin=False)
                    db.session.add(new_user)
                    db.session.commit()   
                    return redirect(url_for("login"))
                else:
                        flash("Please include country calling code!")
        except Exception as e:
            flash("Please enter a valid IC Number.")
            print(e)
    return render_template("register.html")

@app.route('/login', methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        usernameInput = request.form["login-username"]
        passwordInput = request.form["login-password"]

        if users.query.filter_by(username = usernameInput).first() and users.query.filter_by(username = usernameInput).first().password == passwordInput:
            if users.query.filter_by(username=usernameInput).first().two_factor_auth == 1:
                attempted_email = users.query.filter_by(username=usernameInput).first().email
                return redirect(url_for("email_2fa", attempted_email=attempted_email))
            session.permanent = True
            session["user"] = usernameInput
            if users.query.filter_by(username=usernameInput).first().isAdmin == True:
                return redirect(url_for("admin"))
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
            user = users.query.filter_by(username=session["user"]).first()
            name = user.username
            email = user.email
            message = request.form.get("message")
            today = date.today()
            today_str = today.strftime('%Y-%m-%d')
            todayPlaceholder = today_str.split('-')
            dateToday = '/'.join(todayPlaceholder[::-1])

            try:
                msg = automatedEmail(message, name)
                to = [email]
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                smtp_user = os.getenv("EMAIL_USER")  # Use environment variables
                smtp_password = os.getenv("EMAIL_PASSWORD").replace('\xa0', ' ')

                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                    smtp.sendmail(from_addr=smtp_user, to_addrs=to, msg=msg.as_string())

                flash(f"Your inquiry has been submitted successfully. Check your email ({email}) for our response!", "success")
                new_support_request = supportlogs(supportRequest=message, supportDate=dateToday, supportUser=user.id)
                db.session.add(new_support_request)
                db.session.commit()
            except Exception as e:
                flash(f"An error occurred while sending the email: {str(e)}", "danger")
            return redirect(url_for("support"))

        return render_template("support.html", profile_Name = session["user"])
@app.route('/check-in', methods=["GET", "POST"])
def check_in():
    if session["user"] and session["user"] != "":
        if request.method=="POST":
            bookingnum = request.form.get('booking_number')
            surnamelast = request.form.get('surname')

            if bookings.query.filter_by(bookingNum = bookingnum).first() :
                if bookings.query.filter_by(bookingNum = bookingnum).first().surname == surnamelast:
                    booking = bookings.query.filter_by(bookingNum = bookingnum).first()
                    booking.isCheckedIn = True
                    db.session.commit()
                    flash("Check-in successful!", "success")
                    return redirect(url_for("home"))
                else:
                    flash("Check-in failed!", "danger")
            else:
                flash("Check-in failed!", "danger")
                
        return render_template("check_in.html", profile_Name = session["user"])
    else:
        return redirect(url_for("register"))

@app.route('/flights', methods=["GET", "POST"])
def flights():
    if "user" in session and session["user"] != "":
        access_token = get_access_token(apiKey, apiSecret)
        trip = request.args.get('trip')
        return_date = request.args.get('return_date')
        passengers = request.args.get('passengers')
        promo_code = request.args.get('promo_code')
        origin_locations = request.args.get('origin_locations')
        destination_locations = request.args.get('destination_locations')
        departure_dates = request.args.get('departure_dates')

        airline_list = {
            "FY" : "Firefly",
            "MH" : "Malaysia Airlines",
            "OD" : "Batik Air",
            "AK" : "AirAsia"
        }

        if trip == "one-way":
            try:
                origin_location = (origin_locations.split(",")[0])
                originCode = origin_location[-4:-1]
                destination_location = (destination_locations.split(",")[0])
                destinationCode = destination_location[-4:-1]
                departure_date = departure_dates.split(",")[0]
                date_object = datetime.strptime(departure_date, "%Y-%m-%d")
                departure_day = date_object.strftime("%A")
                passengerNum = int(passengers[0])
                flights = get_flights(originCode, destinationCode, passengerNum, departure_date, access_token)
                flight_details = extract_flight_details(flights)
                if flight_details == []:
                    flash(f"Sorry, there are no flights for this trip. ({origin_location} to {destination_location})")
                    return redirect(url_for("home"))
                priceList = []
                for flight in flight_details:
                    if promo_code == "KUANTAN20" and destinationCode == "KUA":
                        flight['price'] = round(float(flight['price'])*0.8, 2)
                    if promo_code == "GANU10" and destinationCode == "TGG":
                        flight['price'] = round(float(flight['price'])*0.9, 2)
                    priceList.append(float(flight['price']))
                priceList.sort()
                print(priceList)

                if request.method == "POST":
                    airlineOneWay = request.form['departure-airline-name-0']
                    flightNoOneWay = request.form['departure-flight-number-0']
                    departuretimeOneWay = request.form['selected-departure-time-0']
                    arrivaltimeOneWay = request.form['selected-arrival-time-0']
                    priceOneWay = request.form['selected-departure-price-0']

                    return redirect(url_for("booking",
                                            profile_Name = session["user"],
                                            airlineOneWay=airlineOneWay,
                                            flightNoOneWay=flightNoOneWay,
                                            departuretimeOneWay=departuretimeOneWay,
                                            arrivaltimeOneWay=arrivaltimeOneWay,
                                            priceOneWay=priceOneWay,
                                            trip=trip,
                                            passengerNum=passengerNum,
                                            origin_location=origin_location,
                                            destination_location=destination_location))

                return render_template(
                    "flights.html",
                    profile_Name = session["user"], 
                    trip=trip,
                    origin_location=origin_location, 
                    destination_location=destination_location, 
                    departure_day=departure_day, 
                    departure_date=departure_date, 
                    passengerNum=passengerNum,
                    flight_details=flight_details,
                    priceList=priceList,
                    airline_list=airline_list
                )
            except Exception as e:
                print(f"Error: {e}")
                flash("No flights available for this trip")
                return redirect(url_for("home"))
        elif trip == "round-trip":
            try:
                origin_location = (origin_locations.split(",")[0])
                originCode = origin_location[-4:-1]
                destination_location = (destination_locations.split(",")[0])
                destinationCode = destination_location[-4:-1]
                departure_date = departure_dates.split(",")[0]
                departure_date_object = datetime.strptime(departure_date, "%Y-%m-%d")
                departure_day = departure_date_object.strftime("%A")
                return_date_object = datetime.strptime(return_date, "%Y-%m-%d")
                return_day = return_date_object.strftime("%A")
                passengerNum = int(passengers[0])

                departure_flights = get_flights(originCode, destinationCode, passengerNum, departure_date, access_token)
                flight_details = extract_flight_details(departure_flights)

                if flight_details == [] or flight_details == "":
                    flash(f"Sorry, there are no flights for this trip. ({origin_location} to {destination_location})")
                    return redirect(url_for("home"))

                priceList = []
                for flight in flight_details:
                    if promo_code == "KUANTAN20" and destinationCode == "KUA":
                        flight['price'] = round(float(flight['price'])*0.8, 2)
                    if promo_code == "GANU10" and destinationCode == "TGG":
                        flight['price'] = round(float(flight['price'])*0.9, 2)
                    priceList.append(flight['price'])
                priceList.sort()
                
                return_flights = get_flights(destinationCode, originCode, passengerNum, return_date, access_token)
                return_flight_details = extract_flight_details(return_flights)
                if return_flight_details == [] or return_flight_details == "":
                    flash(f"Sorry, there are no flights for this trip. ({destination_location} to {origin_location})")
                    return redirect(url_for("home"))
                
                returnPriceList = []
                for flight in return_flight_details:
                    if promo_code == "KUANTAN20" and originCode == "KUA":
                        flight['price'] = round(float(flight['price'])*0.8, 2)
                    if promo_code == "GANU10" and originCode == "TGG":
                        flight['price'] = round(float(flight['price'])*0.9, 2)
                    returnPriceList.append(flight['price'])
                returnPriceList.sort()

                if request.method == "POST":
                    airlineDeparture = request.form['departure-airline-name-0']
                    flightNumDeparture = request.form['departure-flight-number-0']
                    departureTimeInitial = request.form['selected-departure-time-0']
                    arrivalTimeInitial = request.form['selected-arrival-time-0']
                    priceDeparture = request.form['selected-departure-price-0']
                    airlineReturn = request.form['return-airline-name-0']
                    flightNumReturn = request.form['return-flight-number-0']
                    departureTimeRound = request.form['return-departure-time-0']
                    arrivalTimeRound = request.form['return-arrival-time-0']
                    priceReturn = request.form['selected-return-price-0']

                    return redirect(url_for("booking",
                                            profile_Name = session["user"],
                                            airlineDeparture=airlineDeparture,
                                            airlineReturn=airlineReturn,
                                            flightNumDeparture=flightNumDeparture,
                                            flightNumReturn=flightNumReturn,
                                            departureTimeInitial=departureTimeInitial,
                                            departureTimeRound=departureTimeRound,
                                            arrivalTimeInitial=arrivalTimeInitial,
                                            arrivalTimeRound=arrivalTimeRound,
                                            priceDeparture=priceDeparture,
                                            priceReturn=priceReturn,
                                            trip=trip,
                                            passengerNum=passengerNum,
                                            origin_location=origin_location,
                                            destination_location=destination_location))

                return render_template(
                    "flights.html",
                    profile_Name = session["user"],
                    trip=trip, 
                    origin_location=origin_location, 
                    destination_location=destination_location, 
                    departure_day=departure_day, 
                    departure_date=departure_date,
                    return_day = return_day,
                    return_date = return_date, 
                    passengerNum=passengerNum,
                    flight_details=flight_details,
                    return_flight_details=return_flight_details,
                    priceList=priceList,
                    returnPriceList=returnPriceList,
                    airline_list=airline_list
                    )
            except Exception as e:
                print(f"Error: {e}")
                flash("No flights available for this trip.")
                return redirect(url_for("home"))
        return render_template("flights.html", profile_Name = session["user"])
    else:
        return redirect(url_for("login"))

@app.route('/flightsmulticity', methods=["GET", "POST"])
def flightsmulticity():
    if "user" in session and session["user"] != "":
        access_token = get_access_token(apiKey, apiSecret)
        trip = request.args.get('trip')
        passengers = request.args.get('passengers')
        promo_code = request.args.get('promo_code')
        origin_locations = request.args.get('origin_locations')
        destination_locations = request.args.get('destination_locations')
        departure_dates = request.args.get('departure_dates')

        airline_list = {
            "FY" : "Firefly",
            "MH" : "Malaysia Airlines",
            "OD" : "Batik Air",
            "AK" : "AirAsia",
            "TR" : "Scoot"
        }
        try:
            originStops = origin_locations.split(",")
            destinationStops = destination_locations.split(",")
            departureDates = departure_dates.split(",")
            stops = [{"origin": originStops[i], "destination": destinationStops[i], "date": departureDates[i]} for i in range(0, len(originStops))]
            days = []
            for stop in stops:
                days.append((datetime.strptime(stop["date"], "%Y-%m-%d")).strftime("%A"))
            passengerNum = int(passengers[0])

            flights = [get_flights(stops[i]["origin"][-4:-1], stops[i]["destination"][-4:-1], passengerNum, stops[i]["date"], access_token) for i in range(0, len(stops))]
            flight_details = [extract_flight_details(flight) for flight in flights]

            priceList = []
            cheapestFlights = []
            for detail in range(0, len(flight_details)):
                if flight_details[detail] == "":
                    flash(f"There are no flights for this trip. ({stops[detail]['origin']} to {stops[detail]['destination']})")
                    return redirect(url_for("home"))
                for item in flight_details[detail]:
                    if promo_code == "KUANTAN20" and stops[detail]['destination'][-4:-1] == "KUA":
                        item['price'] = round(float(item['price'])*0.8, 2)
                    if promo_code == "GANU10" and stops[detail]['destination'][-4:-1] == "TGG":
                        item['price'] = round(float(item['price'])*0.9, 2)
                    priceList.append(item['price'])
                priceList.sort()
                cheapestFlights.append(priceList[0])
                priceList = []

            if request.method == "POST":
                chosenFlightList = []
                for i in range(0, len(stops)):
                    chosenFlight = {}
                    chosenFlight['airline'] = request.form[f"depature-airline-name-{i}"]
                    chosenFlight['flightNumber'] = request.form[f'departure-flight-number-{i}']
                    chosenFlight['departureTime'] = request.form[f'selected-departure-time-{i}']
                    chosenFlight['arrivalTime'] = request.form[f'selected-arrival-time-{i}']
                    chosenFlight['price'] = request.form[f'selected-departure-price-{i}']
                    chosenFlightList.append(chosenFlight)
                    print(chosenFlightList)
                    chosenFlightListSerialized = json.dumps(chosenFlightList)
                    stopsSerialized = json.dumps(stops)
                print(passengerNum)
                return redirect(url_for("booking",
                                        chosenFlightList=chosenFlightListSerialized,
                                        trip=trip,
                                        passengerNum=passengerNum,
                                        stops=stopsSerialized,
                                        profile_Name = session["user"]))
            
            return render_template(
                "flightsmulticity.html",
                profile_Name = session["user"], 
                trip=trip,
                stops=stops,
                days=days,
                passengerNum=passengerNum,
                cheapestFlights=cheapestFlights,
                flight_details=flight_details,
                airline_list=airline_list
            )
        except Exception as e:
            print(f"{e}")
            flash("No flights available for this trip.")
            return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

@app.route('/settings', methods=["GET", "POST"])
def settings():
    if "user" in session and session["user"] != "":
        current_user = users.query.filter_by(username=session["user"]).first()
        isToggled = current_user.two_factor_auth
        if request.method == "POST":
            new_name = request.form.get("new-full-name")
            new_username = request.form.get("new-username")
            new_ic = request.form.get("new-ic")
            new_phone = request.form.get("new-hp-no")
            new_email = request.form.get("new-email")

            if users.query.filter(users.username == new_username, users.id != current_user.id).first():
                flash("Username already exists!", "danger")
            elif users.query.filter(users.icNumber == new_ic, users.id != current_user.id).first():
                flash("IC number already exists!", "danger")
            elif users.query.filter(users.phoneNumber == new_phone, users.id != current_user.id).first():
                flash("Phone number already exists!", "danger")
            elif users.query.filter(users.email == new_email, users.id != current_user.id).first():
                flash("Email already exists!", "danger")
            else:
                current_user.name = new_name
                current_user.username = new_username
                current_user.icNumber = new_ic
                current_user.phoneNumber = new_phone
                current_user.email = new_email
                db.session.commit()
                session["user"] = current_user.username
                flash("Profile updated successfully!", "success")
            return redirect(url_for("settings", profile_Name = session["user"], user=current_user, isToggled=isToggled))
        
        return render_template("settings.html", profile_Name = session["user"], user=current_user, isToggled=isToggled)
    else:
        return redirect(url_for("login"))
    
@app.route('/change_password', methods=["POST"])
def change_password():
    if "user" in session and session["user"] != "":
        current_user = users.query.filter_by(username=session["user"]).first()
        current_password = request.form.get("reg-password")
        new_password = request.form.get("new-password")

        if current_user.password == current_password:
            current_user.password = new_password
            db.session.commit()
            flash("Password changed successfully!", "success")
        else:
            flash("Invalid current password. Please try again.", "error")

        return redirect(url_for("settings"))
    else:
        return redirect(url_for("login"))

@app.route('/toggleAuth', methods=["GET", "POST"])
def toggleAuth():
    if "user" in session and session["user"] != "":
        if request.method == "POST":
            isToggledOn = request.form.get('toggle-2fa')
            curUser = users.query.filter_by(username=session["user"]).first()
            if isToggledOn == "2fa-on" and curUser.two_factor_auth == 0:
                curUser.two_factor_auth = 1
                db.session.commit()
        return redirect(url_for("settings"))
    else:
        return redirect(url_for("login"))

@app.route('/booking', methods=["GET", "POST"])
def booking():
    if "user" in session and session["user"] != "":
        dataList = []
        tripType = request.args.get('trip')
        rowTag = {0:"A", 1:"B", 2:"C", 3:"D", 4:"E", 5:"F"}
        

        quadrants = {
            "top": {f"{i}-{rowTag[j]}" for i in range(0, 5) for j in range(0, 6)},
            "left": {f"{i}-{rowTag[j]}" for i in range(0, 10) for j in range(0, 3)},
            "bottom": {f"{i}-{rowTag[j]}" for i in range(5, 10) for j in range(0, 6)},
            "right": {f"{i}-{rowTag[j]}" for i in range(0, 10) for j in range(3, 6)},
        }

        if tripType == "one-way":
            data = {}
            data["airline"] = request.args.get('airlineOneWay')
            data["flightNumber"] = request.args.get('flightNoOneWay')
            data["departureTime"] = str(request.args.get('departuretimeOneWay')).strip().split("T")[1]
            data["arrivalTime"] = str(request.args.get('arrivaltimeOneWay')).strip().split("T")[1]
            data["date"] = str(request.args.get('departuretimeOneWay')).strip().split("T")[0]
            data["price"] = request.args.get('priceOneWay')
            data["originLocation"] = request.args.get('origin_location')
            data["destinationLocation"] = request.args.get('destination_location')
            dataList.append(data)

            taken_seats = {
                booking.seatNum
                for booking in bookings.query.filter_by(flightNum=dataList[0]["flightNumber"]).all()
                if booking and datetime.strptime(booking.date, "%Y-%m-%d").date() >= datetime.utcnow().date()
            }
            quadrant_taken = {key: len(taken_seats & seats) for key, seats in quadrants.items()}
            quadrant_taken_json = json.dumps(quadrant_taken)

            passengerNum = int(str(request.args.get('passengerNum'))[0])
            if request.method == "POST":
                bookingUserID = users.query.filter_by(username=session["user"]).first().id
                for i in range(1, passengerNum+1):
                    uniqueBookingNum = False
                    while (uniqueBookingNum == False):
                            bookingNum = "".join(str(chr(random.randint(65, 90))) if random.randint(0, 1) else str(random.randint(0, 9)) for _ in range(5))
                            if not bookings.query.filter_by(bookingNum=bookingNum).first():
                                uniqueBookingNum = True
                    first_name = request.form.get(f"first-name-{i}")
                    surname = request.form.get(f"surname-{i}")
                    ic_number = request.form.get(f"ic-number-{i}")
                    phone_number = request.form.get(f"phone-number-{i}")
                    seat_selection = request.form.get(f"chosen-seat-{i-1}")

                    new_booking = bookings(
                        bookingNum = bookingNum,
                        firstName = first_name,
                        surname = surname,
                        icNum = ic_number,
                        phoneNum = phone_number,
                        origin = dataList[0]["originLocation"],
                        destination = dataList[0]["destinationLocation"],
                        departureTime = dataList[0]["departureTime"],
                        arrivalTime = dataList[0]["arrivalTime"],
                        date = dataList[0]["date"],
                        airline = dataList[0]["airline"],
                        flightNum = dataList[0]["flightNumber"],
                        seatNum = seat_selection,
                        isCheckedIn = False,
                        bookingUserID = bookingUserID
                        )
                    db.session.add(new_booking)
                    db.session.commit()
                flash("Booking details captured successfully!", "success")
                return redirect(url_for("home"))
            
            return render_template(
                "booking.html",
                rowDict=rowTag, 
                taken_seats=taken_seats,
                taken_seats_json = json.dumps(list(taken_seats)),
                quadrant_taken_json=quadrant_taken_json, 
                dataList=dataList, 
                passengerNum = passengerNum,
                tripType=tripType, 
                profile_Name = session["user"]
            )

        elif tripType == "round-trip":
            dataDeparture = {}
            dataReturn = {}
            dataDeparture["airline"] = request.args.get('airlineDeparture')
            dataDeparture["flightNumber"] = request.args.get('flightNumDeparture')
            dataDeparture["departureTime"] = str(request.args.get('departureTimeInitial')).strip().split("T")[1]
            dataDeparture["arrivalTime"] = str(request.args.get('arrivalTimeInitial')).strip().split("T")[1]
            dataDeparture["date"] = str(request.args.get('departureTimeInitial')).strip().split("T")[0]
            dataDeparture["price"] = request.args.get('priceDeparture')
            dataDeparture["originLocation"] = request.args.get('origin_location')
            dataDeparture["destinationLocation"] = request.args.get('destination_location')

            taken_seats_departure = {
                booking.seatNum
                for booking in bookings.query.filter_by(flightNum=dataDeparture["flightNumber"]).all()
                if booking and datetime.strptime(booking.date, "%Y-%m-%d").date() >= datetime.utcnow().date()
            }
            quadrant_taken_departure = {key: len(taken_seats_departure & seats) for key, seats in quadrants.items()}
            
            dataReturn["airline"] = request.args.get('airlineReturn')
            dataReturn["flightNumber"] = request.args.get('flightNumReturn')
            dataReturn["departureTime"] = str(request.args.get('departureTimeRound')).strip().split("T")[1]
            dataReturn["arrivalTime"] = str(request.args.get('arrivalTimeRound')).strip().split("T")[1]
            dataReturn["date"] = str(request.args.get('departureTimeRound')).strip().split("T")[0]
            dataReturn["price"] = request.args.get('priceReturn')
            dataReturn["originLocation"] = request.args.get('destination_location')
            dataReturn["destinationLocation"] = request.args.get('origin_location')

            taken_seats_return = {
                booking.seatNum
                for booking in bookings.query.filter_by(flightNum=dataReturn["flightNumber"]).all()
                if booking and datetime.strptime(booking.date, "%Y-%m-%d").date() >= datetime.utcnow().date()
            }
            quadrant_taken_return = {key: len(taken_seats_return & seats) for key, seats in quadrants.items()}
            quadrant_taken = [quadrant_taken_departure, quadrant_taken_return]
            taken_seats = [list(taken_seats_departure), list(taken_seats_return)]
            quadrant_taken_json = quadrant_taken

            passengerNum = int(str(request.args.get('passengerNum'))[0])
            dataList = [dataDeparture, dataReturn]

            if request.method == "POST":
                bookingUserID = users.query.filter_by(username=session["user"]).first().id
                count = 0
                for i in range(1, passengerNum+1):
                    for j in range(0, len(dataList)):
                        uniqueBookingNum = False
                        while (uniqueBookingNum == False):
                            bookingNum = "".join(str(chr(random.randint(65, 90))) if random.randint(0, 1) else str(random.randint(0, 9)) for _ in range(5))
                            if not bookings.query.filter_by(bookingNum=bookingNum).first():
                                uniqueBookingNum = True
                        first_name = request.form.get(f"first-name-{i}")
                        surname = request.form.get(f"surname-{i}")
                        ic_number = request.form.get(f"ic-number-{i}")
                        phone_number = request.form.get(f"phone-number-{i}")
                        seat_selection = request.form.get(f"chosen-seat-{count}")#[j]
                        origin = dataList[j]["originLocation"]
                        destination = dataList[j]["destinationLocation"]
                        departureTime = dataList[j]["departureTime"]
                        arrivalTime = dataList[j]["arrivalTime"]
                        date = dataList[j]["date"]
                        airline = dataList[j]["airline"]
                        flightNum = dataList[j]["flightNumber"]

                        count += 1

                        new_booking = bookings(
                        bookingNum = bookingNum,
                        firstName = first_name,
                        surname = surname,
                        icNum = ic_number,
                        phoneNum = phone_number,
                        origin = origin,
                        destination = destination,
                        departureTime = departureTime,
                        arrivalTime = arrivalTime,
                        date = date,
                        airline = airline,
                        flightNum = flightNum,
                        seatNum = seat_selection,
                        isCheckedIn = False,
                        bookingUserID = bookingUserID
                        )
                        db.session.add(new_booking)
                        db.session.commit()

                flash("Booking details captured successfully!", "success")
                return redirect(url_for("home"))

            return render_template(
                "booking.html", 
                rowDict=rowTag, 
                taken_seats=taken_seats,
                taken_seats_json = None,
                quadrant_taken_json=quadrant_taken_json,
                dataList=dataList, 
                passengerNum=passengerNum, 
                tripType=tripType, 
                profile_Name = session["user"]
                )
        elif tripType == "multi-city":
            try:
                flightList = json.loads(request.args.get('chosenFlightList'))
                stops = json.loads(request.args.get('stops'))
                taken_seats = []
                quadrant_taken_json = []
                passengerNum = int(str(request.args.get('passengerNum'))[0])

                for i in range(0, len(stops)):
                    data = {}
                    data["airline"] = flightList[i]['airline']
                    data["flightNumber"] = flightList[i]['flightNumber']
                    data["departureTime"] = str(flightList[i]['departureTime']).strip().split("T")[1]
                    data["arrivalTime"] = str(flightList[i]['arrivalTime']).strip().split("T")[1]
                    data["date"] = str(stops[i]["date"]).strip().split("T")[0]
                    data["price"] = flightList[i]['price']
                    data["originLocation"] = stops[i]["origin"]
                    data["destinationLocation"] = stops[i]["destination"]
                    dataList.append(data)

                    takenSeatFlight = {
                        booking.seatNum
                        for booking in bookings.query.filter_by(flightNum=flightList[i]["flightNumber"]).all()
                        if booking and datetime.strptime(booking.date, "%Y-%m-%d").date() >= datetime.utcnow().date()
                    }
                    quadrantTakenFlight = {key: len(takenSeatFlight & seats) for key, seats in quadrants.items()}
                    taken_seats.append(list(takenSeatFlight))
                    quadrant_taken_json.append(quadrantTakenFlight)

                if request.method == "POST":
                    count = 0
                    bookingUserID = users.query.filter_by(username=session["user"]).first().id
                    for i in range(1, passengerNum+1):
                        for j in range(0, len(dataList)):
                            uniqueBookingNum = False
                            while (uniqueBookingNum == False):
                                bookingNum = "".join(str(chr(random.randint(65, 90))) if random.randint(0, 1) else str(random.randint(0, 9)) for _ in range(5))
                                if not bookings.query.filter_by(bookingNum=bookingNum).first():
                                    uniqueBookingNum = True
                            first_name = request.form.get(f"first-name-{i}")
                            surname = request.form.get(f"surname-{i}")
                            ic_number = request.form.get(f"ic-number-{i}")
                            phone_number = request.form.get(f"phone-number-{i}")
                            seat_selection = request.form.get(f"chosen-seat-{count}")
                            origin = dataList[j]["originLocation"]
                            destination = dataList[j]["destinationLocation"]
                            departureTime = dataList[j]["departureTime"]
                            arrivalTime = dataList[j]["arrivalTime"]
                            date = dataList[j]["date"]
                            airline = dataList[j]["airline"]
                            flightNum = dataList[j]["flightNumber"]
                            
                            count += 1

                            new_booking = bookings(
                            bookingNum = bookingNum,
                            firstName = first_name,
                            surname = surname,
                            icNum = ic_number,
                            phoneNum = phone_number,
                            origin = origin,
                            destination = destination,
                            departureTime = departureTime,
                            arrivalTime = arrivalTime,
                            date = date,
                            airline = airline,
                            flightNum = flightNum,
                            seatNum = seat_selection,
                            isCheckedIn = False,
                            bookingUserID = bookingUserID
                            )
                            db.session.add(new_booking)
                            db.session.commit()

                    flash("Booking details captured successfully!", "success")
                    return redirect(url_for("home"))


                return render_template(
                "booking.html",
                rowDict=rowTag, 
                taken_seats=taken_seats,
                taken_seats_json = None,
                quadrant_taken_json=quadrant_taken_json,  
                dataList=dataList, 
                passengerNum=passengerNum, 
                tripType=tripType, 
                profile_Name = session["user"]
                )
            except Exception as e:
                print(f"{e}")
        # return redirect(url_for("home"))   
        return render_template("booking.html", dataList=dataList, tripType=tripType, profile_Name = session["user"])  
    else:
        return redirect(url_for("login"))

@app.route('/forgotpassword', methods=["GET", "POST"])
def forgotpassword():
    if request.method == "POST":
        session.pop('_flashes', None)
        usernameForgotPassword = request.form.get("user-forgot-pass")
        isUser = users.query.filter_by(username=usernameForgotPassword).first()
        if isUser:
            email = isUser.email
            newPass = "".join(str(random.randint(0,9)) for i in range(0,8))
            isUser.password = newPass
            db.session.commit()

            msg = MIMEMultipart()
            msg['Subject'] = "New Password."

            text = f'''
        <html>
        <body>
            <p>Dear <b>{usernameForgotPassword}</b>,</p>
            <p>This is your new <i>TEMPORARY</i> password.</p>
            <b>{newPass}</b>
            <p>You may change this password later in the <i>Change Password</i> menu in the settings.</p>
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

            to = [email]
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = os.getenv("EMAIL_USER")  # Use environment variables
            smtp_password = os.getenv("EMAIL_PASSWORD").replace('\xa0', ' ')

            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_password)
                smtp.sendmail(from_addr=smtp_user, to_addrs=to, msg=msg.as_string())
            flash(f"A new password has been sent to you via email ({email})", "success")
        else:
            flash("That Username does not exist!")
    return render_template('forgot.html')

@app.route('/profile')
def profile():
    if "user" in session and session["user"] != "":
        current_user = users.query.filter_by(username=session["user"]).first()
        recent_flights = bookings.query.filter_by(bookingUserID=current_user.id).all()
        return render_template("profile.html", profile_Name=session["user"], user=current_user, recent_flights=recent_flights)
    else:
        return redirect(url_for("login"))

@app.route('/cancel_flight')
def cancel_flight():
    booking_num = request.args.get('bookingNum')
    if booking_num and bookings.query.filter_by(bookingNum = booking_num):
        db.session.query(bookings).filter_by(bookingNum = booking_num).delete()
        db.session.commit()
    flash(f"Flight with booking number: {booking_num} cancelled!")
    return redirect(url_for("home"))

@app.route('/ticket/<booking_id>')
def ticket(booking_id):

    booking = bookings.query.filter_by(bookingNum = booking_id).first()
    if booking.isCheckedIn == False:
        flash("Flight not checked in!")
        return redirect(url_for("home"))

    # Render the HTML with flight details
    return render_template('ticket.html', booking=booking)

@app.route('/email_2fa', methods=["GET", "POST"])
def email_2fa():
    try:
        attempted_email = request.args.get('attempted_email')
        if attempted_email is None:
            return redirect(url_for("login"))

        u = users.query.filter_by(email=attempted_email).first()
        user = u.username

        # Generate a new code only if one doesn't already exist in the session
        if "auth_code" not in session:
            session["auth_code"] = "".join(
                str(chr(random.randint(65, 90))) if random.randint(0, 1) else str(random.randint(0, 9))
                for _ in range(4)
            )
            threading.Thread(
                target=send2FAEmail, 
                args=(user, attempted_email, session["auth_code"], current_app.root_path)
            ).start()
        
        flash(f"An email has been sent to {attempted_email}!")

        if request.method == "POST":
            attemptedCode = request.form.get('auth-code')
            print("User Entered Code:", attemptedCode)
            print("Stored Code:", session["auth_code"])

            if attemptedCode == session["auth_code"]:
                session.permanent = True
                session["user"] = user
                session.pop("auth_code", None)  # Remove the code after successful login
                if u.isAdmin == True:
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("home"))

        return render_template('email_2fa.html', email=attempted_email, user=user)

    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for("login"))


def send2FAEmail(user, attempted_email, code, app_root):
    time.sleep(5)
    msg = MIMEMultipart()
    msg['Subject'] = "Email Two Factor Authentication"
    text = f'''
<html>
<body>
    <p>Dear <b>{user}</b>,</p>
    <p>This is your 4 DIGIT CODE. Enter it on our website to proceed with verification.</p>
    <b>{code}</b>
    <p>It is advised to not share this code with anyone.</p>
    <br>
    <p>Didn't send this request? You can change your password in the Change Password menu!</p>
    <p>
        Regards,<br>
        <b>SkyLink Co.<b>
    </p>
</body>
</html>
'''
    msg.attach(MIMEText(text, "html", "utf-8"))

    image_path = os.path.join(app_root, 'static', 'img', 'logo.png')
    if image_path and os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), name=os.path.basename(image_path))
            msg.attach(img)

    to = [attempted_email]
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = os.getenv("EMAIL_USER")  # Use environment variables
    smtp_password = os.getenv("EMAIL_PASSWORD").replace('\xa0', ' ')

    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.sendmail(from_addr=smtp_user, to_addrs=to, msg=msg.as_string())

@app.route('/booking_receipt', methods=["GET"])
def booking_receipt():
    # booking_id = request.args.get("bookingNum")
    return render_template('receipt.html')

@app.route('/admin')
def admin():
    if "user" in session and session["user"] != "":
        if users.query.filter_by(username=session["user"]).first().isAdmin != True:
            return redirect(url_for("home"))
        booking_list = bookings.query.join(users, users.id == bookings.bookingUserID).all()
        request_list = supportlogs.query.join(users, users.id == supportlogs.supportUser).all()
        return render_template("admin.html", profile_Name=session["user"], booking_list=booking_list, request_list = request_list)
    else:
        return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
