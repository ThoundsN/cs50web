import json
import os

from flask import Flask, session, request, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import requests



app = Flask(__name__)
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

    userRecord = db.execute("SELECT * FROM users WHERE username= :username AND password= :password", {"username":username,"password":password }).fetchone()
    if userRecord is None:
        return render_template("mainpage.html", message = "Incorrect password or username")

    session["uid"] = userRecord['id']
    session["username"] = userRecord['username']
    return render_template("dashboard.html", username = session.get("username"))


@app.route("/logout")
def logout():
    session.clear()
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
    username = session.get("username")
    return render_template("dashboard.html",username=username)

@app.route("/register", methods = ["POST"])
def register():
    return render_template("register.html")

@app.route("/search", methods=["POST"])
def search():
    text = request.form.get("text")
    username = session.get("username")
    data =db.execute("SELECT * FROM books WHERE author iLIKE '%"+text+"%' OR title iLIKE '%"+text+"%' OR isbn iLIKE '%"+text+"%'").fetchall()
    books = []
    for x in data:
        books.append(x)
    if len(books) == 0:
        message = "Nothing found, please make sure you enter the correct query"
    else:
        message = "These are the books you might  be interested in!"
    return render_template("dashboard.html", message = message, books = books, username = username)


@app.route("/isbn/<string:isbn>", methods=["GET","POST"])
def bookpage(isbn):
    if session is None:
        message = "Please login in the first place"
        return render_template("mainpage.html", message = message)
    username = session.get("username")
    hasreview  = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username= :username",{"username":username,"isbn":isbn}).fetchone()
    if request.method == "POST" and hasreview is not None:
        warning = "Sorry, You have already reviewd this book"
    elif request.method == "POST" and hasreview is None:
        review = request.form.get("textarea")
        rating = request.form.get("stars")
        db.execute("INSERT INTO reviews (isbn, review, rating, username) VALUES (:a,:b,:c,:d)",{"a":isbn,"b":review,"c":rating,"d":username})
        db.commit()

    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "XfLii2ANGvBM0dq48QHGA", "isbns":isbn})
    average_rating  = res.json()['books'][0]['average_rating']
    work_ratings_count = res.json()['books'][0]['work_ratings_count']

    return render_template("bookdetail.html", average_rating =average_rating, work_ratings_count = work_ratings_count,
                           data = data,  reviews = reviews, username = username )


@app.route("/api/<string:isbn>")
def api(isbn):
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if data is None:
        return render_template("error.html", message = "ISBN INCORRECT")
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "XfLii2ANGvBM0dq48QHGA", "isbns": isbn})
    average_rating = res.json()['books'][0]['average_rating']
    work_ratings_count = res.json()['books'][0]['work_ratings_count']
    x ={
        "title":data.title,
        "author": data.author,
        "year": data.year,
        "isbn": data.isbn,
        "work_ratings_count " : work_ratings_count,
        "average_rating ": average_rating

    }
    api = json.dumps(x)
    return render_template("api.json", api = api)