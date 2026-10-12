from database.db import get_db

def save_note(title, filename, pages):
    db = get_db()
    cursor = db.execute("INSERT INTO notes(title, filename) VALUES (?, ?)", (title, filename))
    note_id = cursor.lastrowid
    db.executemany(
        "INSERT INTO note_pages(note_id, page_number, text) VALUES (?, ?, ?)",
        [(note_id, p["page_number"], p["text"]) for p in pages]
    )
    db.commit()
    return note_id

def list_notes():
    db = get_db()
    return db.execute("""
        SELECT n.*,
          (SELECT COUNT(*) FROM note_pages p WHERE p.note_id=n.id) AS page_count
        FROM notes n ORDER BY n.created_at DESC
    """).fetchall()

def get_note(note_id):
    db = get_db()
    note = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not note:
        return None
    pages = db.execute(
        "SELECT page_number, text FROM note_pages WHERE note_id=? ORDER BY page_number",
        (note_id,)
    ).fetchall()
    return {"id": note["id"], "title": note["title"], "filename": note["filename"],
            "created_at": note["created_at"], "pages": [dict(p) for p in pages]}

def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    db.commit()
