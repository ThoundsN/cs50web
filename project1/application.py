import os

from flask import Flask, session, request, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import validators


app = Flask(__name__)
import requests
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "kZfYFDBnljvMpQSr0H3Vg", "isbns": "9781632168146"})
# print(res.json())
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def mainpage():
    if "uid" in session:
        return render_template("dashboard.html", session = session )
    else:
        return render_template("mainpage.html")

@app.route("/login", methods = ["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    userRecord = db.execute("SELECT * FROM users WHERE username= :username", {"username":username})
    if userRecord is None:
        return render_template("mainpage.html", message = "No such account")
    row = {}
    print(userRecord)
    for r in userRecord:
        print(type(r.__dict__))
        row = row + r.__dict__
    if row["password"] != password:
        return render_template("mainpage.html", message = "Password incorrect")

    session["uid"] = row["id"]
    session["username"] = row["username"]
    return render_template("dashboard.html", session = session)

@app.route("/logout")
def logout():
    if "uid" in session:
        del session['uid']
    return render_template("mainpage.html")

@app.route("/newuser", methods = ["POST"])
def newuser():
    username = request.form.get("username")
    password = request.form.get("password")



    if len(username)<5 or len(username)>15 or len(password)<6 or len(password)>20:
        return render_template("register.html", message = f"Length of username and password should be 5 to 15 and 6 to 20 seperately")
    if db.execute("SELECT * FROM users WHERE username= :username",{"username": username}).rowcount != 0:
        return render_template("register.html", message =f"username {username} has already been taken " )

    db.execute(
        "INSERT INTO users (username, password) VALUES (:username, :password)",
        {"username": username, "password": password})
    db.commit()
    return render_template("mainpage.html")

@app.route("/dashboard", methods = ["POST"])
def dashboard():

    return render_template("dashboard.html")

@app.route("/register", methods = ["POST"])
def register():
    return render_template("register.html")



def rowtodict(resultproxy):
    d = {}
    for rowproxy in resultproxy: