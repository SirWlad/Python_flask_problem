import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    session['s_name'] = "Shares symbol"
    if request.method == "POST":
        action = request.form.get('action')
        session['s_name'] = request.form.get('stock_name')
        return redirect(action)
    else:
        cash = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )
        sum = db.execute(
            "SELECT stock_name, SUM(qty) AS total_qty, ABS(SUM(price)) AS total_price FROM ops WHERE user_id = ? GROUP BY stock_name ORDER BY stock_name ASC", session["user_id"])
        diff = [''] * len(sum)
        new_price = [0.0] * len(sum)
        new_data = [0.0] * len(sum)
        for i in range(len(sum)):
            new_data[i] = lookup(sum[i]['stock_name'])
            new_price[i] = new_data[i]['price'] * sum[i]['total_qty']
            value = (new_price[i] / abs(sum[i]['total_price']) - 1) * 100
            diff[i] = f"{value:,.2f}"
        return render_template("index.html", cash=cash[0]['cash'], operations=sum, new_price=new_price, diff=diff, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    cash = db.execute(
        "SELECT cash FROM users WHERE id = ?", session["user_id"]
    )
    if request.method == "POST":
        data = lookup(request.form.get("symbol"))
        if data:
            qty = request.form.get("shares")
            if not qty.isdigit() or float(qty) % 1 != 0 or float(qty) < 0:
                return apology("Buy doesn't handle fractional, negative, and non-numeric shares", 400)
            else:
                qty = int(request.form.get("shares"))
                price = float(data['price'])
                ability = cash[0]['cash'] - qty * price
                if ability >= 0:
                    db.execute(
                        "INSERT INTO ops (user_id, stock_name, stock_price, qty, price, date) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], data['symbol'], price, qty, - (
                            qty * price), datetime.now()
                    )
                    db.execute(
                        "UPDATE users SET cash = ? WHERE id = ?", ability, session["user_id"]
                    )
                    return redirect("/")
                else:
                    return apology("Not enought cash", 400)
        else:
            return apology("invalid stock symbol", 400)
    else:
        return render_template("buy.html", cash=usd(cash[0]['cash']), symbol=session['s_name'])


@app.route("/history")
@login_required
def history():
    session['s_name'] = "Shares symbol"
    cash = db.execute(
        "SELECT cash FROM users WHERE id = ?", session["user_id"]
    )
    ops = db.execute("SELECT * FROM ops WHERE user_id = ? ORDER BY date DESC", session["user_id"])
    if ops:
        return render_template("history.html", operations=ops, cash=cash[0]['cash'], usd=usd)
    else:
        return apology("History is clear", 400)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    session['s_name'] = "Shares symbol"
    if request.method == "POST":
        data = lookup(request.form.get("symbol"))
        if data:
            return render_template("symbol.html", symbol=data['symbol'], price=usd(data['price']))
        else:
            return apology("invalid stock symbol", 400)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if rows:
            return apology("username is already taken", 400)
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords must be the same", 400)

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get(
                "username"), generate_password_hash(request.form.get("password"))
        )

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        # Remember which user has registered
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

        # Query database for username
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    cash = db.execute(
        "SELECT cash FROM users WHERE id = ?", session["user_id"]
    )
    sum = db.execute(
        "SELECT stock_name, SUM(qty) AS total_qty, SUM(price) AS total_price FROM ops WHERE user_id = ? GROUP BY stock_name", session["user_id"])

    if request.method == "POST":
        if db.execute("SELECT stock_name FROM ops WHERE user_id = ? AND stock_name = ? GROUP BY stock_name", session["user_id"], request.form.get("symbol")):
            data = lookup(request.form.get("symbol"))
            if data:
                qty = request.form.get("shares")
                if not qty.isdigit() or float(qty) % 1 != 0 or float(qty) < 0:
                    return apology("Sell doesn't handle fractional, negative, and non-numeric shares", 400)
                else:
                    qty = - int(request.form.get("shares"))
                    if sum[0]['total_qty'] + qty < 0:
                        return apology("You dont have that much stocks", 400)
                    else:
                        price = float(data['price'])
                        change = cash[0]['cash'] - qty * price
                        db.execute(
                            "INSERT INTO ops (user_id, stock_name, stock_price, qty, price, date) VALUES (?, ?, ?, ?, ?, ?)", session[
                                "user_id"], data['symbol'], price, qty, (-1 * qty * price), datetime.now()
                        )
                        db.execute(
                            "UPDATE users SET cash = ? WHERE id = ?", change, session["user_id"]
                        )
                        return redirect("/")
            else:
                return apology("invalid stock symbol", 400)
        else:
            return apology("You dont have that stock symbol", 400)
    else:
        return render_template("sell.html", cash=usd(cash[0]['cash']), symbols=sum, symbol=session['s_name'])
