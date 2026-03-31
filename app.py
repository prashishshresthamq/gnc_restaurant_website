from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gnc-brews-cms-secret-change-this-in-production"

# ── Flask-Login setup ────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the admin panel."
login_manager.login_message_category = "error"

ADMIN_FILE    = "data/admin.json"
DATA_FILE     = "data/site_data.json"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ── Admin user model ─────────────────────────────────────────────
class AdminUser(UserMixin):
    id = "admin"
    def __init__(self, username):
        self.username = username

def load_admin():
    if not os.path.exists(ADMIN_FILE):
        defaults = {
            "username": "admin",
            "password": generate_password_hash("admin123"),
            "first_login": True
        }
        with open(ADMIN_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults
    with open(ADMIN_FILE) as f:
        return json.load(f)

def save_admin(data):
    with open(ADMIN_FILE, "w") as f:
        json.dump(data, f, indent=2)

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        admin = load_admin()
        return AdminUser(admin["username"])
    return None

# ── Site data helpers ────────────────────────────────────────────
DEFAULT_DATA = {
    "hours": {
        "mon_fri": "5:30am - 3:00pm",
        "saturday": "6:00am - 3:00pm",
        "sunday": "7:00am - 2:00pm"
    },
    "contact": {
        "address": "786 Old Princes Highway, Sydney NSW",
        "instagram": "gnc.brews2025",
        "phone": ""
    },
    "menu": [
        {"id": 1, "name": "The Big Brekkie", "category": "Breakfast", "description": "Bacon, eggs, avocado, sourdough toast, roasted tomato.", "price": "22.00", "image": ""},
        {"id": 2, "name": "Eggs Benedict",   "category": "Brunch",    "description": "Poached eggs on toasted muffin with hollandaise sauce.", "price": "19.00", "image": ""},
        {"id": 3, "name": "Specialty Lattes","category": "Coffee",    "description": "Seasonal latte specials crafted by our baristas.",       "price": "6.50",  "image": ""},
        {"id": 4, "name": "House Smoothies", "category": "Drinks",    "description": "Thick house-blended smoothies in seasonal flavours.",     "price": "12.00", "image": ""},
        {"id": 5, "name": "Avo Toast",       "category": "Brunch",    "description": "Smashed avocado on sourdough with feta and microgreens.", "price": "18.00", "image": ""},
        {"id": 6, "name": "Daily Bakes",     "category": "Pastries",  "description": "Fresh croissants and scrolls from local artisan bakers.", "price": "5.50",  "image": ""},
    ],
    "gallery": [],
    "hero": {
        "tagline": "Good Coffee, Great Food.",
        "subtitle": "Breakfast & Lunch in the heart of Sydney",
        "description": "A neighbourhood cafe where every cup is crafted with care and every plate is made to linger over."
    }
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file_key):
    if file_key not in request.files:
        return None
    file = request.files[file_key]
    if file.filename == "":
        return None
    if file and allowed_file(file.filename):
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return filename
    return None

# ── Public website ───────────────────────────────────────────────

@app.route("/")
def website():
    data = load_data()
    return render_template("website.html", data=data)

# ── Auth routes ──────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        admin = load_admin()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == admin["username"] and check_password_hash(admin["password"], password):
            user = AdminUser(username)
            login_user(user, remember=request.form.get("remember") == "on")
            next_page = request.args.get("next")
            if admin.get("first_login"):
                flash("Please change your default password before continuing.", "warning")
                return redirect(url_for("change_password"))
            flash("Welcome back!", "success")
            if next_page and next_page.startswith("/admin"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect username or password.", "error")
    return render_template("login.html")

@app.route("/admin/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        admin = load_admin()
        current_pw = request.form.get("current_password", "")
        new_pw     = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")
        if not check_password_hash(admin["password"], current_pw):
            flash("Current password is incorrect.", "error")
        elif len(new_pw) < 8:
            flash("New password must be at least 8 characters.", "error")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "error")
        else:
            admin["password"] = generate_password_hash(new_pw)
            admin["first_login"] = False
            save_admin(admin)
            flash("Password changed successfully!", "success")
            return redirect(url_for("dashboard"))
    return render_template("change_password.html")

# ── Admin routes (all @login_required) ──────────────────────────

@app.route("/admin")
@login_required
def dashboard():
    data = load_data()
    all_bookings = load_bookings()
    pending = sum(1 for b in all_bookings if b["status"] == "pending")
    return render_template("dashboard.html", data=data,
                           menu_count=len(data["menu"]),
                           gallery_count=len(data["gallery"]),
                           pending_bookings=pending)

@app.route("/admin/hours", methods=["GET", "POST"])
@login_required
def hours():
    data = load_data()
    if request.method == "POST":
        data["hours"]["mon_fri"]  = request.form["mon_fri"]
        data["hours"]["saturday"] = request.form["saturday"]
        data["hours"]["sunday"]   = request.form["sunday"]
        save_data(data)
        flash("Opening hours updated!", "success")
        return redirect(url_for("hours"))
    return render_template("hours.html", data=data)

@app.route("/admin/hero", methods=["GET", "POST"])
@login_required
def hero():
    data = load_data()
    if request.method == "POST":
        data["hero"]["tagline"]     = request.form["tagline"]
        data["hero"]["subtitle"]    = request.form["subtitle"]
        data["hero"]["description"] = request.form["description"]
        save_data(data)
        flash("Hero section updated!", "success")
        return redirect(url_for("hero"))
    return render_template("hero.html", data=data)

@app.route("/admin/contact", methods=["GET", "POST"])
@login_required
def contact():
    data = load_data()
    if request.method == "POST":
        data["contact"]["address"]   = request.form["address"]
        data["contact"]["instagram"] = request.form["instagram"]
        data["contact"]["phone"]     = request.form["phone"]
        save_data(data)
        flash("Contact info updated!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", data=data)

@app.route("/admin/menu")
@login_required
def menu():
    data = load_data()
    return render_template("menu.html", data=data)

@app.route("/admin/menu/add", methods=["GET", "POST"])
@login_required
def menu_add():
    data = load_data()
    if request.method == "POST":
        image_filename = upload_image("image")
        new_id = max((item["id"] for item in data["menu"]), default=0) + 1
        data["menu"].append({
            "id": new_id,
            "name": request.form["name"],
            "category": request.form["category"],
            "description": request.form["description"],
            "price": request.form["price"],
            "image": image_filename or ""
        })
        save_data(data)
        flash(f"'{request.form['name']}' added to menu!", "success")
        return redirect(url_for("menu"))
    categories = sorted({item["category"] for item in data["menu"]})
    return render_template("menu_form.html", data=data, item=None, categories=categories, action="Add")

@app.route("/admin/menu/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def menu_edit(item_id):
    data = load_data()
    item = next((i for i in data["menu"] if i["id"] == item_id), None)
    if not item:
        flash("Menu item not found.", "error")
        return redirect(url_for("menu"))
    if request.method == "POST":
        image_filename = upload_image("image")
        item["name"]        = request.form["name"]
        item["category"]    = request.form["category"]
        item["description"] = request.form["description"]
        item["price"]       = request.form["price"]
        if image_filename:
            item["image"] = image_filename
        save_data(data)
        flash(f"'{item['name']}' updated!", "success")
        return redirect(url_for("menu"))
    categories = sorted({i["category"] for i in data["menu"]})
    return render_template("menu_form.html", data=data, item=item, categories=categories, action="Edit")

@app.route("/admin/menu/delete/<int:item_id>", methods=["POST"])
@login_required
def menu_delete(item_id):
    data = load_data()
    data["menu"] = [i for i in data["menu"] if i["id"] != item_id]
    save_data(data)
    flash("Menu item deleted.", "success")
    return redirect(url_for("menu"))

@app.route("/admin/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    data = load_data()
    if request.method == "POST":
        files = request.files.getlist("photos")
        added = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file.filename)}"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                data["gallery"].append({"filename": filename, "caption": ""})
                added += 1
        save_data(data)
        flash(f"{added} photo(s) uploaded!", "success")
        return redirect(url_for("gallery"))
    return render_template("gallery.html", data=data)

@app.route("/admin/gallery/delete/<filename>", methods=["POST"])
@login_required
def gallery_delete(filename):
    data = load_data()
    data["gallery"] = [g for g in data["gallery"] if g["filename"] != filename]
    save_data(data)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    flash("Photo deleted.", "success")
    return redirect(url_for("gallery"))

@app.route("/api/site-data")
def api_site_data():
    return jsonify(load_data())

# ── Bookings ─────────────────────────────────────────────────────

BOOKINGS_FILE = "data/bookings.json"

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE) as f:
            return json.load(f)
    return []

def save_bookings(bookings):
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)

@app.route("/book", methods=["POST"])
def book():
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip()
    phone   = request.form.get("phone", "").strip()
    date    = request.form.get("date", "").strip()
    time    = request.form.get("time", "").strip()
    guests  = request.form.get("guests", "").strip()
    message = request.form.get("message", "").strip()

    if not all([name, email, date, time, guests]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("website") + "#booking")

    bookings = load_bookings()
    bookings.append({
        "id":         len(bookings) + 1,
        "name":       name,
        "email":      email,
        "phone":      phone,
        "date":       date,
        "time":       time,
        "guests":     guests,
        "message":    message,
        "status":     "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_bookings(bookings)
    flash("Booking request sent! We will confirm shortly.", "success")
    return redirect(url_for("website") + "#booking")

@app.route("/admin/bookings")
@login_required
def bookings():
    all_bookings = load_bookings()
    all_bookings = sorted(all_bookings, key=lambda x: x["created_at"], reverse=True)
    counts = {
        "pending":   sum(1 for b in all_bookings if b["status"] == "pending"),
        "confirmed": sum(1 for b in all_bookings if b["status"] == "confirmed"),
        "cancelled": sum(1 for b in all_bookings if b["status"] == "cancelled"),
        "total":     len(all_bookings)
    }
    return render_template("bookings.html", bookings=all_bookings, counts=counts)

@app.route("/admin/bookings/<int:booking_id>/status", methods=["POST"])
@login_required
def booking_status(booking_id):
    all_bookings = load_bookings()
    booking = next((b for b in all_bookings if b["id"] == booking_id), None)
    if booking:
        booking["status"] = request.form.get("status", "pending")
        save_bookings(all_bookings)
        flash(f"Booking #{booking_id} marked as {booking['status']}.", "success")
    return redirect(url_for("bookings"))

@app.route("/admin/bookings/<int:booking_id>/delete", methods=["POST"])
@login_required
def booking_delete(booking_id):
    all_bookings = load_bookings()
    all_bookings = [b for b in all_bookings if b["id"] != booking_id]
    save_bookings(all_bookings)
    flash("Booking deleted.", "success")
    return redirect(url_for("bookings"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
