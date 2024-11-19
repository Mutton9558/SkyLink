from flask import *

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/home')
def redirectToDefault():
    return redirect(url_for("home"))

@app.route('/register')
def register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)