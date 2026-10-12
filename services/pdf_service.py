import fitz  # PyMuPDF

def extract_pdf_pages(path):
    """Return [{'page_number': 1, 'text': '...'}, ...]."""
    pages = []
    with fitz.open(path) as document:
        for index, page in enumerate(document):
            pages.append({"page_number": index + 1, "text": page.get_text("text").strip()})
    return pages
