# NoteWise AI — AI-Powered Question Answering System for College Notes

A mini-project built with Python, Flask, SQLite, PyMuPDF, scikit-learn, HTML, CSS and JavaScript.

## Features
- Upload and store text-based PDF college notes.
- Extract page text and retain page numbers.
- Ask questions using TF-IDF similarity search over the selected PDF.
- Answers use relevant note passages and include page references.
- Low-evidence fallback instead of pretending to know an answer.
- Generate fill-in-the-blank practice quizzes from extracted sentences.
- Store quiz scores and question history in SQLite.
- Responsive browser interface.

## Important note about the AI
This starter version uses local information retrieval (TF-IDF), not a paid external LLM API. It is lightweight, works without API keys, and is easier to demonstrate locally. It returns excerpts from the PDF rather than writing fluent generative answers. For best results, use selectable-text PDFs. Scanned/image-only PDFs need OCR before uploading.

## Requirements
- Python 3.10 or newer (3.11 recommended)
- pip
- A modern browser

## Install and run — Windows PowerShell
```powershell
cd college_notes_qa
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```
If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```
Or use Command Prompt:
```bat
cd college_notes_qa
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Install and run — macOS / Linux / Git Bash
```bash
cd college_notes_qa
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. Keep the terminal open while using the app. Stop the server with `Ctrl+C`.

## First-time use
1. Open the website.
2. Upload a text-based PDF (maximum 20 MB).
3. Open the uploaded note.
4. Ask a question about a topic covered in that PDF.
5. Select **Generate practice quiz** to take a quiz.
6. Open **Progress** to view saved activity.

## Project structure
```text
college_notes_qa/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── database/
│   ├── __init__.py
│   └── db.py
├── services/
│   ├── __init__.py
│   ├── pdf_service.py
│   ├── notes_service.py
│   └── qa_service.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── note.html
│   ├── quiz.html
│   ├── quiz_result.html
│   └── progress.html
├── static/
│   ├── app.js
│   └── style.css
├── uploads/          # created automatically
└── instance/         # database created automatically
```

## Troubleshooting
- **`python` command not found:** try `py` on Windows or `python3` on macOS/Linux.
- **Virtual environment activation is blocked:** use the PowerShell command above or Command Prompt activation.
- **Package installation fails:** upgrade pip and confirm internet access. Python 3.11 is recommended.
- **PDF uploads but no text is found:** it may be a scanned PDF. OCR it first, or use a text-based PDF.
- **Port 5000 is already in use:** change the final line in `app.py` to `app.run(debug=True, port=5001)` and open `http://127.0.0.1:5001`.
- **Reset local database:** stop the app, delete `instance/college_notes.db`, then start it again. This deletes saved notes/history records; also delete files in `uploads/` if you want to clear uploaded PDFs.
- **Before public deployment:** replace the development secret key, disable debug mode, add authentication/authorization, and review file-upload security. This project is intended for a local academic demonstration.

## Suggested mini-project description
**Problem:** Students spend time searching long PDF notes for answers and revision material.

**Solution:** A web application that extracts text from uploaded notes, retrieves relevant passages for a student's question, cites page numbers, creates practice questions, and tracks quiz progress.

**Core technologies:** Python, Flask, SQLite, PyMuPDF, TF-IDF information retrieval, JavaScript, HTML and CSS.

## Academic honesty / limitations
This project is a functional starter implementation. Test it with your own syllabus PDFs, document the test cases/results, and be prepared to explain PDF extraction, TF-IDF similarity, source grounding, database tables, and quiz generation in your project viva.
