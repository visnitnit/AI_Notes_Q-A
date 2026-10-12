from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from config import Config
from database.db import init_db, get_db
from services.pdf_service import extract_pdf_pages
from services.qa_service import answer_question, generate_quiz
from services.notes_service import save_note, list_notes, get_note, delete_note

app = Flask(__name__)
app.config.from_object(Config)
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
Path(app.config["INSTANCE_FOLDER"]).mkdir(parents=True, exist_ok=True)
init_db(app.config["DATABASE"])

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html", notes=list_notes())

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf_file")
    title = (request.form.get("title") or "").strip()
    if not file or not file.filename:
        flash("Choose a PDF file first.", "error")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Only PDF files are supported.", "error")
        return redirect(url_for("index"))
    safe_name = secure_filename(file.filename)
    if not title:
        title = Path(safe_name).stem
    # Unique filename prevents accidental overwrites.
    import uuid
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = Path(app.config["UPLOAD_FOLDER"]) / stored_name
    file.save(destination)
    try:
        pages = extract_pdf_pages(destination)
        if not any(page["text"].strip() for page in pages):
            destination.unlink(missing_ok=True)
            flash("No readable text was found. If this is a scanned PDF, run OCR first.", "error")
            return redirect(url_for("index"))
        note_id = save_note(title, stored_name, pages)
        flash(f"Uploaded '{title}' successfully.", "success")
        return redirect(url_for("note_detail", note_id=note_id))
    except Exception as exc:
        destination.unlink(missing_ok=True)
        flash(f"Could not read that PDF: {exc}", "error")
        return redirect(url_for("index"))

@app.route("/notes/<int:note_id>")
def note_detail(note_id):
    note = get_note(note_id)
    if not note:
        flash("Note not found.", "error")
        return redirect(url_for("index"))
    return render_template("note.html", note=note)

@app.route("/api/notes/<int:note_id>/ask", methods=["POST"])
def ask(note_id):
    note = get_note(note_id)
    if not note:
        return jsonify({"error": "Note not found."}), 404
    payload = request.get_json(silent=True) or request.form
    question = (payload.get("question") or "").strip()
    if len(question) < 3:
        return jsonify({"error": "Please enter a question with at least 3 characters."}), 400
    result = answer_question(note, question)
    db = get_db()
    db.execute(
        "INSERT INTO question_history(note_id, question, answer, created_at) VALUES (?, ?, ?, datetime('now'))",
        (note_id, question, result["answer"])
    )
    db.commit()
    return jsonify(result)

@app.route("/notes/<int:note_id>/quiz", methods=["GET", "POST"])
def quiz(note_id):
    note = get_note(note_id)
    if not note:
        flash("Note not found.", "error")
        return redirect(url_for("index"))
    questions = generate_quiz(note, count=15)
    if request.method == "POST":
        answers = request.form
        score = 0
        for i, q in enumerate(questions):
            if answers.get(f"q{i}") == str(q["correct_index"]):
                score += 1
        db = get_db()
        db.execute(
            "INSERT INTO quiz_attempts(note_id, score, total, created_at) VALUES (?, ?, ?, datetime('now'))",
            (note_id, score, len(questions))
        )
        db.commit()
        return render_template("quiz_result.html", note=note, questions=questions, answers=answers, score=score)
    return render_template("quiz.html", note=note, questions=questions)

@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note_route(note_id):
    note = get_note(note_id)
    if note:
        try:
            (Path(app.config["UPLOAD_FOLDER"]) / note["filename"]).unlink(missing_ok=True)
        except OSError:
            pass
        delete_note(note_id)
        flash("Note deleted.", "success")
    return redirect(url_for("index"))

@app.route("/progress")
def progress():
    db = get_db()
    rows = db.execute("""
        SELECT n.id, n.title,
               (SELECT COUNT(*) FROM question_history q WHERE q.note_id=n.id) AS questions,
               (SELECT COUNT(*) FROM quiz_attempts a WHERE a.note_id=n.id) AS attempts,
               (SELECT COALESCE(MAX(CAST(score AS REAL)/NULLIF(total,0)*100),0)
                FROM quiz_attempts a WHERE a.note_id=n.id) AS best_score
        FROM notes n ORDER BY n.created_at DESC
    """).fetchall()
    return render_template("progress.html", rows=rows)

@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 20 MB.", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
