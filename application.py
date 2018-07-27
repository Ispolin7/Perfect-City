import os.path
import time
from flask import Flask, jsonify, render_template, redirect, request, session, url_for, send_from_directory
from flask_session import Session
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from tempfile import mkdtemp
from helpers import login_required
from cs50 import SQL

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# find city for registration


@app.route("/find_city")
def find():
    q = request.args.get("request") + "%"
    place = db.execute("SELECT * FROM citys WHERE ((postal_code LIKE :q) OR (place_name LIKE :q) OR (admin_name1 LIKE :q)) LIMIT 5", q=q)
    return jsonify(place)

# registration


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # если гет - возвращаем форму

    if request.method == "GET":
        return render_template("register.html")
    # если пост - проверяем и записываем в базу

    else:

        user = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if user:
            return render_template("register.html", message="Username is busy")
        else:
            add = db.execute("INSERT INTO users (username, hash, email, city) VALUES (:username, :hash, :email, :city)",
                             username=request.form.get("username"),
                             hash=generate_password_hash(request.form.get("password")),
                             email=request.form.get("email"),
                             city=request.form.get("city"))
        user = db.execute("SELECT * FROM users WHERE id=:id", id=add)
        session["user_id"] = add
        session["username"] = user[0]["username"]
        print(session["user_id"])
        print(session["username"])
        return redirect("/")

# sign in


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", message="Incorrect username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        myCity = db.execute("SELECT * FROM citys WHERE postal_code = :city",
                            city=rows[0]["city"])
        session["city"] = myCity[0]["place_name"]
        print(session["city"])

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

# INDEX


@app.route("/")
@login_required
def index():
    """Render map"""
    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")
    else:
        user = db.execute("SELECT * FROM users WHERE id = :auth", auth=session["user_id"])
        city = db.execute("SELECT * FROM citys WHERE  postal_code = :mySity", mySity=user[0]["city"])
        session["city"] = city[0]["place_name"]
    return render_template("index.html", key=os.environ.get("API_KEY"), user=user[0], city=city[0], currentCity=session["city"])

# add new place


@app.route("/add_place", methods=["POST"])
@login_required
def add():
    if not request.form.get("name"):
        lat = request.form.get("lat")
        lng = request.form.get("lng")
        return render_template("addPlace.html", lat=lat, lng=lng, currentCity=session["city"])
    else:
        file = request.files['file']
        # return file.filename
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            rows = db.execute("SELECT * FROM users WHERE id = :auth", auth=session["user_id"])
            user = db.execute("INSERT INTO places (name, description, lat, lng, image, created_by, city, add_date) VALUES (:name, :description, :lat, :lng, :image, :created_by, :city, :add_date)",
                              name=request.form.get("name"),
                              description=request.form.get("description"),
                              lat=request.form.get("lat"),
                              lng=request.form.get("lng"),
                              image=filename,
                              created_by=session["user_id"],
                              city=rows[0]["city"],
                              add_date=int(time.time()))
            return redirect("/")

# see all place + sort place


@app.route("/places")
@login_required
def places():

    if not request.args.get("postalCode"):
        raise RuntimeError("invalid city")

    sort = request.args.get("sort")

    if sort == "new":
        current_time = int(time.time())
        places = db.execute("SELECT * FROM places WHERE (city = :postalCode AND completed_date IS NULL AND add_date > :sort_time)",
                            postalCode=request.args.get("postalCode"),
                            sort_time=current_time - 604800)  # previous week
        return jsonify(places)

    elif sort == "my":
        places = db.execute("SELECT * FROM places WHERE (city = :postalCode AND completed_date IS NULL AND created_by = :my)",
                            postalCode=request.args.get("postalCode"),
                            my=session["user_id"])
        return jsonify(places)
    elif sort == "comment":
        add = []
        places = db.execute("SELECT * FROM places WHERE (city = :postalCode AND completed_date IS NULL)",
                            postalCode=request.args.get("postalCode"))
        for place in places:
            comment = db.execute("SELECT * FROM comments WHERE place_id = :current_place",
                                 current_place=place['id'])
            if comment:
                add.append(place)

        return jsonify(add)

    elif sort == "completed":
        places = db.execute("SELECT * FROM places WHERE (city = :postalCode AND completed_date IS NOT NULL)",
                            postalCode=request.args.get("postalCode"))
        return jsonify(places)

    else:
        places = db.execute("SELECT * FROM places WHERE (city = :postalCode AND completed_date IS NULL)",
                            postalCode=request.args.get("postalCode"))
        return jsonify(places)

# see details for place


@app.route('/places/<place_id>')
@login_required
def show_information(place_id):
    place = db.execute("SELECT * FROM places WHERE id = :place_id", place_id=place_id)
    comments = db.execute("SELECT * FROM comments WHERE place_id = :place_id", place_id=place_id)
    return render_template("place.html", place=place[0], currentCity=session["city"], comments=comments)

# add comment to place


@app.route('/places/<place_id>/add_comment', methods=["POST"])
@login_required
def add_comment(place_id):
    comment = request.form.get("comment")
    add = db.execute("INSERT INTO comments (description, created_by, place_id) VALUES (:description, :created_by, :place_id )",
                     description=request.form.get("comment"),
                     created_by=session["username"],
                     place_id=place_id)
    return redirect('/places/' + place_id)

# Completed place


@app.route('/places/<place_id>/update', methods=["POST"])
@login_required
def update(place_id):
    place = db.execute("UPDATE places SET completed_date = :currentTime WHERE id = :placeId",
                       currentTime=int(time.time()), placeId=place_id)
    return redirect('/')