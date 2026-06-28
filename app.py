"""
app.py — Main Flask application
Routes:
  GET  /              → Home / submission form
  POST /analyze       → Run detection, save, redirect to result
  GET  /result/<id>   → Show result page
  POST /feedback/<id> → Save user feedback
  GET  /history       → All submissions (last 50)
  GET  /register      → Registration form
  POST /register      → Process registration
  GET  /login         → Login form
  POST /login         → Process login
  GET  /logout        → Clear session
  GET  /api/stats     → JSON stats (for AJAX)
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from database import (
    init_db, register_user, login_user,
    save_submission, get_submission,
    get_all_submissions, get_stats, save_feedback
)
from ml_model import detect_fake_news

app = Flask(__name__)
app.secret_key = "fnd_secret_2024_umt"   # change in production


# ── Initialize DB on startup ───────────────────────────────────────────────────
with app.app_context():
    init_db()


# ── Home / Analyze form ────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    stats = get_stats()
    return render_template("index.html", stats=stats)


@app.route("/analyze", methods=["POST"])
def analyze():
    title  = request.form.get("title", "").strip()
    text   = request.form.get("news_text", "").strip()
    url    = request.form.get("source_url", "").strip()

    if not text or len(text) < 20:
        flash("Please enter at least 20 characters of news text.", "error")
        return redirect(url_for("index"))

    result = detect_fake_news(text)
    user_id = session.get("user_id")
    sub_id  = save_submission(user_id, title, text, url, result)

    return redirect(url_for("show_result", submission_id=sub_id))


# ── Result page ────────────────────────────────────────────────────────────────
@app.route("/result/<int:submission_id>")
def show_result(submission_id):
    sub = get_submission(submission_id)
    if not sub:
        flash("Result not found.", "error")
        return redirect(url_for("index"))
    return render_template("result.html", sub=sub)


# ── Feedback ───────────────────────────────────────────────────────────────────
@app.route("/feedback/<int:submission_id>", methods=["POST"])
def feedback(submission_id):
    if "user_id" not in session:
        flash("Login to submit feedback.", "error")
        return redirect(url_for("login"))
    is_correct = request.form.get("is_correct") == "1"
    comment    = request.form.get("comment", "").strip()
    save_feedback(submission_id, session["user_id"], is_correct, comment)
    flash("Thanks for your feedback!", "success")
    return redirect(url_for("show_result", submission_id=submission_id))


# ── History ────────────────────────────────────────────────────────────────────
@app.route("/history")
def history():
    user_id = session.get("user_id")
    # logged-in users see their own; guests see all (public)
    submissions = get_all_submissions(user_id=user_id, limit=50)
    return render_template("history.html", submissions=submissions)


# ── Auth: Register ─────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        email    = request.form.get("email", "").strip()

        if not username or not password or not email:
            flash("All fields are required.", "error")
            return render_template("index.html", show_register=True, stats=get_stats())

        success, msg = register_user(username, password, email)
        if success:
            flash(msg, "success")
            return redirect(url_for("login"))
        else:
            flash(msg, "error")

    return render_template("index.html", show_register=True, stats=get_stats())


# ── Auth: Login ────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = login_user(username, password)
        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("index.html", show_login=True, stats=get_stats())


# ── Auth: Logout ───────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("index"))


# ── API: Stats ─────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
