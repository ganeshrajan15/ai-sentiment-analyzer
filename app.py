import sqlite3
from flask import Flask, render_template, request, redirect, jsonify
from transformers import pipeline

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from flask_bcrypt import Bcrypt

# =========================
# APP SETUP
# =========================
app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey123"

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# USER CLASS
# =========================
class User(UserMixin):

    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):

    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:
        return User(user[0], user[1])

    return None


# =========================
# AI MODEL
# =========================

sentiment_model = pipeline(
    "sentiment-analysis",
    model="sshleifer/tiny-distilbert-base-uncased-finetuned-sst-2-english"
)


def analyze(text):

    result = sentiment_model(text)[0]

    label = result["label"]
    score = result["score"]

    if label == "POSITIVE":
        sentiment = "Positive 😃"
    else:
        sentiment = "Negative 😡"

    return sentiment, score


# =========================
# DATABASE
# =========================
def init_db():

    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    # sentiments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            sentiment TEXT,
            score REAL
        )
    """)

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_data(text, sentiment, score):

    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sentiments (text, sentiment, score) VALUES (?, ?, ?)",
        (text, sentiment, score)
    )

    conn.commit()
    conn.close()


def fetch_all():

    conn = sqlite3.connect("sentiment.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sentiments")

    data = cursor.fetchall()

    conn.close()

    return data


# initialize db
init_db()


# =========================
# ROUTES
# =========================

@app.route("/")
def home():

    if current_user.is_authenticated:
        return render_template("index.html")

    return redirect("/login")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = sqlite3.connect("sentiment.db")
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_pw)
            )

            conn.commit()

        except:
            conn.close()
            return "Username already exists"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("sentiment.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):

            logged_user = User(user[0], user[1])

            login_user(logged_user)

            return redirect("/")

        return "Invalid username or password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")


# =========================
# PREDICT
# =========================
@app.route("/predict", methods=["POST"])
@login_required
def predict():

    text = request.form["text"]

    sentiment, score = analyze(text)

    insert_data(text, sentiment, score)

    return render_template(
        "index.html",
        prediction=sentiment,
        score=round(score, 2),
        input_text=text
    )


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
@login_required
def dashboard():

    data = fetch_all()

    positive = len([d for d in data if "Positive" in d[2]])
    negative = len([d for d in data if "Negative" in d[2]])

    return render_template(
        "dashboard.html",
        data=data,
        positive=positive,
        negative=negative
    )


# =========================
# API
# =========================
@app.route("/api/sentiment", methods=["POST"])
def api_sentiment():

    data = request.json["text"]

    sentiment, score = analyze(data)

    return jsonify({
        "sentiment": sentiment,
        "score": float(score)
    })


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)