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
import random

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

    # fetch a new token
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
        "max": "4"
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
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
    if session["user"] and session["user"] != "":
        # if request.method == "POST":
            # ic_number = request.form.get("ic_number") 
            # email = request.form.get("email")


            # user = users.query.filter_by(icNumber=ic_number, email=email).first()

            # if user:

            #     flash(f"Check-in successful! Welcome, {user.name}.", "success")
            #     return redirect(url_for("check_in"))
            # else:

            #     flash("Invalid IC Number or Email. Please try again.", "error")
            #     return redirect(url_for("check_in"))
        return render_template("check_in.html", profile_Name = session["user"])
    else:
        return redirect(url_for("register"))

@app.route('/flights', methods=["GET", "POST"])
def flights():
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
            priceList = []
            # departureTimeList = []
            # arrivalTimeList = []
            # flightNumList = []
            # airlineList = []

            for flight in flight_details:
            #     print(f"Flight: {flight['flight_number']}, Airline: {flight['airline']}, "
            #     f"Departure: {flight['departure_time']}, Arrival: {flight['arrival_time']}, Price: {flight['price']}")
            #     flightNumList.append(flight['flight_number'])
            #     airlineList.append(flight['airline'])
            #     departureTimeList.append(flight['departure_time'])
            #     arrivalTimeList.append(flight['arrival_time'])
            
                priceList.append(flight['price'])
            priceList.sort()

            if request.method == "POST":
                airlineOneWay = request.form['depature-airline-name-0']
                flightNoOneWay = request.form['departure-flight-number-0']
                departuretimeOneWay = request.form['selected-departure-time-0']
                arrivaltimeOneWay = request.form['selected-arrival-time-0']
                priceOneWay = request.form['selected-departure-price-0']

                return redirect(url_for("booking",
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

            priceList = []
            for flight in flight_details:
                priceList.append(flight['price'])
            priceList.sort()
            
            return_flights = get_flights(destinationCode, originCode, passengerNum, return_date, access_token)
            return_flight_details = extract_flight_details(return_flights)
            
            returnPriceList = []
            for flight in return_flight_details:
                returnPriceList.append(flight['price'])
            returnPriceList.sort()
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
    return render_template("flights.html", profile_Name = session["user"])

@app.route('/flightsmulticity', methods=["GET", "POST"])
def flightsmulticity():
    if "user" in session and session["user"] != "":
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
            "AK" : "AirAsia"
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
            for detail in flight_details:
                for item in detail:
                    priceList.append(item['price'])
                priceList.sort()
                cheapestFlights.append(priceList[0])
                priceList = []
            
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
            return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

@app.route('/settings', methods=["GET", "POST"])
def settings():
    if "user" in session and session["user"] != "":
        current_user = users.query.filter_by(username=session["user"]).first()
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
            return redirect(url_for("settings", profile_Name = session["user"], user=current_user))
        
        return render_template("settings.html", profile_Name = session["user"], user=current_user)
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

@app.route('/booking', methods=["GET", "POST"])
def booking():
    if "user" in session and session["user"] != "":
        data = {}
        tripType = request.args.get('trip')
        if tripType == "one-way":

            data["airline"] = request.args.get('airlineOneWay')
            data["flightNumber"] = request.args.get('flightNoOneWay')
            data["departureTime"] = str(request.args.get('departuretimeOneWay')).strip().split("T")[1]
            data["arrivalTime"] = str(request.args.get('arrivaltimeOneWay')).strip().split("T")[1]
            data["date"] = str(request.args.get('departuretimeOneWay')).strip().split("T")[0]
            data["price"] = request.args.get('priceOneWay')
            data["passengerNum"] = request.args.get('passengerNum')
            data["originLocation"] = request.args.get('origin_location')
            data["destinationLocation"] = request.args.get('destination_location')

            if request.method == "POST":
                first_name = request.form.get("first_name")
                surname = request.form.get("surname")
                ic_number = request.form.get("ic_number")
                phone_number = request.form.get("phone_number")
                seat_selection = request.form.get("seat_selection")
                flash("Booking details captured successfully!", "success")
                return redirect(url_for("booking"))
            
            return render_template("booking.html", data=data, tripType=tripType)
            # Assuming static/preset data for now
            # start_location = "Kuala Lumpur International Airport (KUL)"
            # destination = "Singapore Changi Airport (SIN)"
            # departure_time = "10:00 AM"
            # estimated_arrival = "12:30 PM"
            # flight_date = "2024-12-20"
            # flight_number = "MH123"

            # Process data or save to the database (if needed)
        return redirect(url_for("home"))     
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
            smtp_password = os.getenv("EMAIL_PASSWORD")

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
        return render_template("profile.html", profile_Name = session["user"])
    else:
        return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
