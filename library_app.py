from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "booknest_secret_123"


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db():

    conn = sqlite3.connect("library.db")

    conn.row_factory = sqlite3.Row

    return conn


# ==============================
# CREATE DATABASE TABLES
# ==============================

def create_tables():

    conn = get_db()


    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)


    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            book_id TEXT NOT NULL,

            book_name TEXT NOT NULL,

            book_number TEXT NOT NULL,

            student_name TEXT NOT NULL,

            issue_date TEXT NOT NULL,

            due_date TEXT NOT NULL,

            status TEXT DEFAULT 'Issued',

            return_date TEXT,

            fine INTEGER DEFAULT 0

        )
    """)


    conn.commit()

    conn.close()


# ==============================
# HOME
# ==============================

@app.route("/library")
def library_home():

    return render_template(
        "library_home.html"
    )


# ==============================
# SIGNUP
# ==============================

@app.route("/library/signup", methods=["GET", "POST"])
def library_signup():

    if request.method == "POST":

        name = request.form["name"].strip()

        username = request.form["username"].strip()

        password = request.form["password"]


        if not name or not username or not password:

            flash(
                "All fields are required!",
                "error"
            )

            return render_template(
                "library_signup.html"
            )


        if len(password) < 4:

            flash(
                "Password must contain at least 4 characters!",
                "error"
            )

            return render_template(
                "library_signup.html"
            )


        conn = get_db()


        try:

            hashed_password = generate_password_hash(
                password
            )


            conn.execute(
                """
                INSERT INTO users
                (name, username, password)

                VALUES (?, ?, ?)
                """,

                (
                    name,
                    username,
                    hashed_password
                )
            )


            conn.commit()

            conn.close()


            flash(
                "Account created successfully! Please login.",
                "success"
            )


            return redirect(
                url_for("library_login")
            )


        except sqlite3.IntegrityError:

            conn.close()


            flash(
                "Username already exists!",
                "error"
            )


            return render_template(
                "library_signup.html"
            )


    return render_template(
        "library_signup.html"
    )


# ==============================
# LOGIN
# ==============================

@app.route("/library/login", methods=["GET", "POST"])
def library_login():

    if request.method == "POST":

        username = request.form["username"].strip()

        password = request.form["password"]


        conn = get_db()


        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,

            (username,)
        ).fetchone()


        conn.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["name"] = user["name"]


            flash(
                "Welcome back, " + user["name"] + "!",
                "success"
            )


            return redirect(
                url_for("library_dashboard")
            )


        flash(
            "Invalid username or password!",
            "error"
        )


    return render_template(
        "library_login.html"
    )


# ==============================
# DASHBOARD
# ==============================

@app.route("/library/dashboard")
def library_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("library_login")
        )


    conn = get_db()


    total_books = conn.execute(
        """
        SELECT COUNT(*)
        FROM books
        """
    ).fetchone()[0]


    issued_books = conn.execute(
        """
        SELECT COUNT(*)
        FROM books
        WHERE status = 'Issued'
        """
    ).fetchone()[0]


    returned_books = conn.execute(
        """
        SELECT COUNT(*)
        FROM books
        WHERE status = 'Returned'
        """
    ).fetchone()[0]


    total_students = conn.execute(
        """
        SELECT COUNT(DISTINCT student_name)
        FROM books
        """
    ).fetchone()[0]


    conn.close()


    return render_template(
        "library_dashboard.html",

        name=session["name"],

        total_books=total_books,

        issued_books=issued_books,

        returned_books=returned_books,

        total_students=total_students
    )


# ==============================
# ISSUE BOOK
# ==============================

@app.route("/library/issue", methods=["GET", "POST"])
def library_issue():

    if "user_id" not in session:

        return redirect(
            url_for("library_login")
        )


    if request.method == "POST":

        book_id = request.form["book_id"].strip()

        book_name = request.form["book_name"].strip()

        book_number = request.form["book_number"].strip()

        student_name = request.form["student_name"].strip()

        issue_date = request.form["issue_date"]

        due_date = request.form["due_date"]


        if not all([
            book_id,
            book_name,
            book_number,
            student_name,
            issue_date,
            due_date
        ]):

            flash(
                "Please fill all fields!",
                "error"
            )

            return render_template(
                "library_issue.html"
            )


        try:

            issue = datetime.strptime(
                issue_date,
                "%Y-%m-%d"
            ).date()


            due = datetime.strptime(
                due_date,
                "%Y-%m-%d"
            ).date()


        except ValueError:

            flash(
                "Invalid date!",
                "error"
            )

            return render_template(
                "library_issue.html"
            )


        if due < issue:

            flash(
                "Due date cannot be before issue date!",
                "error"
            )

            return render_template(
                "library_issue.html"
            )


        conn = get_db()


        existing_book = conn.execute(
            """
            SELECT *
            FROM books

            WHERE book_id = ?

            AND status = 'Issued'
            """,

            (book_id,)
        ).fetchone()


        if existing_book:

            conn.close()


            flash(
                "This book is already issued!",
                "error"
            )


            return render_template(
                "library_issue.html"
            )


        conn.execute(
            """
            INSERT INTO books

            (
                book_id,
                book_name,
                book_number,
                student_name,
                issue_date,
                due_date,
                status,
                fine
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                book_id,
                book_name,
                book_number,
                student_name,
                issue_date,
                due_date,
                "Issued",
                0
            )
        )


        conn.commit()

        conn.close()


        flash(
            "Book issued successfully!",
            "success"
        )


        return render_template(
            "library_success.html",

            book_name=book_name,

            student_name=student_name,

            issue_date=issue_date
        )


    return render_template(
        "library_issue.html"
    )


# ==============================
# BOOKS
# ==============================

@app.route("/library/books")
def library_books():

    if "user_id" not in session:

        return redirect(
            url_for("library_login")
        )


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = get_db()


    if search:

        books = conn.execute(
            """
            SELECT *
            FROM books

            WHERE book_name LIKE ?

            OR book_id LIKE ?

            OR student_name LIKE ?

            OR book_number LIKE ?

            ORDER BY id DESC
            """,

            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()


    else:

        books = conn.execute(
            """
            SELECT *
            FROM books
            ORDER BY id DESC
            """
        ).fetchall()


    conn.close()


    return render_template(
        "library_books.html",

        books=books,

        search=search
    )


# ==============================
# RETURN BOOK
# ==============================

@app.route("/library/return/<int:book_id>")
def return_book(book_id):

    if "user_id" not in session:

        return redirect(
            url_for("library_login")
        )


    conn = get_db()


    book = conn.execute(
        """
        SELECT *
        FROM books
        WHERE id = ?
        """,

        (book_id,)
    ).fetchone()


    if not book:

        conn.close()


        flash(
            "Book record not found!",
            "error"
        )


        return redirect(
            url_for("library_books")
        )


    if book["status"] == "Returned":

        conn.close()


        flash(
            "This book has already been returned!",
            "error"
        )


        return redirect(
            url_for("library_books")
        )


    today = date.today()


    due_date = datetime.strptime(
        book["due_date"],
        "%Y-%m-%d"
    ).date()


    late_days = (
        today - due_date
    ).days


    if late_days > 0:

        fine = late_days * 5

    else:

        fine = 0


    return_date = today.strftime(
        "%Y-%m-%d"
    )


    conn.execute(
        """
        UPDATE books

        SET

            status = 'Returned',

            return_date = ?,

            fine = ?

        WHERE id = ?
        """,

        (
            return_date,
            fine,
            book_id
        )
    )


    conn.commit()

    conn.close()


    flash(
        f"Book returned successfully! Fine: ₹{fine}",
        "success"
    )


    return redirect(
        url_for("library_books")
    )


# ==============================
# HISTORY
# ==============================

@app.route("/library/history")
def library_history():

    if "user_id" not in session:

        return redirect(
            url_for("library_login")
        )


    conn = get_db()


    history = conn.execute(
        """
        SELECT *
        FROM books
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    return render_template(
        "library_history.html",

        history=history
    )


# ==============================
# LOGOUT
# ==============================

@app.route("/library/logout")
def library_logout():

    session.clear()


    flash(
        "You have been logged out successfully.",
        "success"
    )


    return redirect(
        url_for("library_home")
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == "__main__":

    create_tables()

    app.run(debug=True)