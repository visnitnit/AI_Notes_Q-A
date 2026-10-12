
import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOPWORDS = set("""
a an the and or but if then than of in on at to for from by with as is are
was were be been being it its this that these those into about what which who
whom when where why how explain describe define discuss write tell give me
please can could would should do does did has have had according chapter
topic notes pdf following state list mention summarize summary about tell me
""".split())


def split_sentences(text):
    """Split text into readable sentences."""
    text = re.sub(r"\s+", " ", text or "").strip()

    if not text:
        return []

    chunks = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text
    )

    return [
        chunk.strip(" •\t-\n")
        for chunk in chunks
        if chunk.strip(" •\t-\n")
    ]


def extract_topic_sections(note):
    """
    Divide PDF text into sections using likely headings.
    Keep the original text and preserve sections across pages.
    """
    sections = []
    current_title = "General Content"
    current_lines = []
    current_page = 1

    heading_keywords = {
        "summary", "graduation", "education", "skills",
        "experience", "objectives", "introduction",
        "conclusion", "definition", "advantages",
        "disadvantages", "applications", "features",
        "projects", "certifications", "achievements",
        "references", "methodology", "results",
        "discussion", "abstract", "requirements",
        "architecture", "implementation", "procedure",
        "algorithm", "theory", "examples", "types"
    }

    def save_section():
        if current_lines:
            sections.append({
                "title": current_title,
                "text": "\n".join(current_lines).strip(),
                "page": current_page
            })

    for page in note.get("pages", []):
        page_number = page.get("page_number", 1)

        for raw_line in (page.get("text") or "").splitlines():
            line = raw_line.strip()

            if not line:
                continue

            words = line.split()
            normalized = line.lower().strip().rstrip(":")
            numbered_heading = bool(
                re.match(r"^\d+(?:\.\d+)*[.)]?\s+\S+", line)
            )

            known_heading = normalized in heading_keywords

            # Recognize short standalone headings, including custom titles.
            short_heading = (
                len(words) <= 8
                and len(line) <= 65
                and not line.endswith((".", ",", ";", "?"))
                and not re.search(
                    r"\b(is|are|was|were|has|have|because|therefore)\b",
                    normalized
                )
            )

            is_heading = (
                numbered_heading
                or known_heading
                or short_heading
            )

            if is_heading:
                save_section()
                current_title = re.sub(
                    r"^\d+(?:\.\d+)*[.)]?\s*",
                    "",
                    line
                ).rstrip(":").strip()
                current_lines = []
                current_page = page_number
            else:
                if not current_lines:
                    current_page = page_number

                current_lines.append(line)

    save_section()

    # If the PDF has no detectable headings, retain its content as one section.
    if not sections:
        all_lines = []

        for page in note.get("pages", []):
            text = (page.get("text") or "").strip()
            if text:
                all_lines.append(text)

        if all_lines:
            sections.append({
                "title": "General Content",
                "text": "\n".join(all_lines),
                "page": 1
            })

    return sections


def _similarity_scores(query, documents):
    """Calculate text similarity safely."""
    if not documents:
        return []

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        matrix = vectorizer.fit_transform([query] + documents)

        scores = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        ).flatten()

        return [float(score) for score in scores]

    except ValueError:
        return [0.0] * len(documents)


def _retrieve(note, question, top_k=10):
    """Retrieve relevant sentences as a fallback."""
    segments = []

    for page in note.get("pages", []):
        page_number = page.get("page_number", "?")

        for sentence in split_sentences(page.get("text", "")):
            segments.append({
                "text": sentence,
                "page": page_number
            })

    if not segments:
        return []

    scores = _similarity_scores(
        question,
        [item["text"] for item in segments]
    )

    ranked = sorted(
        zip(scores, segments),
        key=lambda item: item[0],
        reverse=True
    )

    return [
        {
            "text": item["text"],
            "page": item["page"],
            "score": score
        }
        for score, item in ranked[:top_k]
        if score > 0.015
    ]


def _find_relevant_section(note, question):
    """Find the single best matching section."""
    sections = extract_topic_sections(note)

    if not sections:
        return None, 0.0

    question_clean = question.strip().lower()
    question_words = {
        word for word in re.findall(r"\b\w+\b", question_clean)
        if word not in STOPWORDS and len(word) > 1
    }

    # Prefer an explicit topic-title match.
    exact_matches = []

    for section in sections:
        title = section["title"].strip().lower()
        title_words = {
            word for word in re.findall(r"\b\w+\b", title)
            if word not in STOPWORDS and len(word) > 1
        }

        if title and (
            title in question_clean
            or question_clean in title
            or (
                title_words
                and title_words.issubset(question_words)
            )
        ):
            exact_matches.append(section)

    if exact_matches:
        # Prefer the longest matching title when titles overlap.
        selected = max(
            exact_matches,
            key=lambda section: len(section["title"])
        )
        return selected, 1.0

    documents = [
        section["title"] + " " + section["text"]
        for section in sections
    ]

    scores = _similarity_scores(question, documents)

    if not scores:
        return None, 0.0

    best_index = max(range(len(scores)), key=lambda i: scores[i])
    best_score = scores[best_index]

    # Check whether the question shares meaningful words with the section.
    selected = sections[best_index]
    section_words = set(
        re.findall(
            r"\b\w+\b",
            (selected["title"] + " " + selected["text"]).lower()
        )
    )

    has_keyword_overlap = bool(question_words & section_words)

    if best_score < 0.025 or not has_keyword_overlap:
        return None, best_score

    return selected, best_score


def answer_question(note, question):
    """
    Return the complete matching section when one can be identified.
    Otherwise, use relevant sentences from the PDF as a fallback.
    """
    question = (question or "").strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "confidence": "low"
        }

    section, section_score = _find_relevant_section(note, question)

    if section and section["text"].strip():
        answer = (
            f"## {section['title']}\n\n"
            f"{section['text']}"
        )

        return {
            "answer": answer,
            "sources": [{
                "page": section["page"],
                "excerpt": section["text"]
            }],
            "confidence": (
                "high" if section_score >= 0.15 else "medium"
            )
        }

    # Fallback when a complete matching section cannot be identified.
    matches = _retrieve(note, question, top_k=10)

    if not matches or matches[0]["score"] < 0.035:
        return {
            "answer": (
                "## Information Not Found\n\n"
                "I couldn't find enough relevant information in "
                "your uploaded PDF to answer confidently.\n\n"
                "Try using keywords from the relevant topic in your notes."
            ),
            "sources": [],
            "confidence": "low"
        }

    # Avoid returning unrelated sentences from the whole document.
    best_score = matches[0]["score"]
    chosen = [
        item for item in matches
        if item["score"] >= max(0.035, best_score * 0.55)
    ][:5]

    answer_lines = ["## Answer", ""]

    for item in chosen:
        answer_lines.extend([
            item["text"],
            ""
        ])

    return {
        "answer": "\n".join(answer_lines).strip(),
        "sources": [
            {
                "page": item["page"],
                "excerpt": item["text"]
            }
            for item in chosen
        ],
        "confidence": (
            "high" if best_score >= 0.18 else "medium"
        )
    }


def _quiz_words(sentence):
    """Extract distinct candidate answer terms."""
    words = re.findall(
        r"\b[A-Za-z][A-Za-z0-9-]{3,}\b",
        sentence
    )

    result = []
    seen = set()

    for word in words:
        lower = word.lower()

        if lower in STOPWORDS:
            continue

        if word.isupper() and len(word) <= 5:
            continue

        if lower not in seen:
            result.append(word)
            seen.add(lower)

    return result


def _make_quiz_statement(sentence, answer_word):
    """Create a fill-in-the-blank statement from a PDF sentence."""
    pattern = re.compile(re.escape(answer_word), re.IGNORECASE)

    clauses = re.split(r"(?<=[,;:])\s+", sentence)

    matching_clauses = [
        clause.strip()
        for clause in clauses
        if pattern.search(clause)
    ]

    suitable = [
        clause for clause in matching_clauses
        if 6 <= len(clause.split()) <= 24
    ]

    statement = (
        max(suitable, key=lambda clause: len(clause.split()))
        if suitable
        else sentence
    )

    words = statement.split()

    if len(words) > 24:
        index = next(
            (
                i for i, word in enumerate(words)
                if pattern.search(
                    re.sub(r"[^A-Za-z0-9-]", "", word)
                )
            ),
            None
        )

        if index is not None:
            start = max(0, index - 11)
            end = min(len(words), start + 24)
            start = max(0, end - 24)

            statement = " ".join(words[start:end])

            if start > 0:
                statement = "... " + statement

            if end < len(words):
                statement += " ..."

    blanked = pattern.sub("________", statement, count=1)

    return blanked if blanked != statement else None


def generate_quiz(note, count=15):
    """
    Generate up to count multiple-choice questions from the PDF.
    The default target is 15; fewer are returned if the notes do not
    contain enough distinct answers and plausible distractors.
    """
    try:
        count = max(1, int(count))
    except (TypeError, ValueError):
        count = 15

    candidates = []

    for page in note.get("pages", []):
        page_number = page.get("page_number", "?")

        for sentence in split_sentences(page.get("text", "")):
            words = _quiz_words(sentence)

            if len(words) >= 2:
                candidates.append({
                    "page": page_number,
                    "sentence": sentence,
                    "words": words
                })

    if not candidates:
        return []

    term_frequency = Counter(
        word.lower()
        for item in candidates
        for word in item["words"]
    )

    candidates.sort(
        key=lambda item: (
            0 if 7 <= len(item["sentence"].split()) <= 35 else 1,
            abs(len(item["sentence"].split()) - 18)
        )
    )

    all_terms = []
    seen_terms = set()

    for item in candidates:
        for word in item["words"]:
            if word.lower() not in seen_terms:
                all_terms.append(word)
                seen_terms.add(word.lower())

    questions = []
    used_answers = set()
    used_statements = set()

    for item in candidates:
        if len(questions) >= count:
            break

        possible_answers = sorted(
            item["words"],
            key=lambda word: (
                0 if 5 <= len(word) <= 14 else 1,
                term_frequency[word.lower()],
                abs(len(word) - 8)
            )
        )

        for answer_word in possible_answers:
            answer_key = answer_word.lower()

            if answer_key in used_answers:
                continue

            blanked = _make_quiz_statement(
                item["sentence"],
                answer_word
            )

            if not blanked:
                continue

            if blanked.lower() in used_statements:
                continue

            distractors = [
                word for word in all_terms
                if word.lower() != answer_key
                and word.lower() not in STOPWORDS
            ]

            distractors.sort(
                key=lambda word: (
                    abs(len(word) - len(answer_word)),
                    term_frequency[word.lower()]
                )
            )

            options = [answer_word]
            seen_options = {answer_key}

            for word in distractors:
                if word.lower() in seen_options:
                    continue

                options.append(word)
                seen_options.add(word.lower())

                if len(options) == 4:
                    break

            # Only keep questions with four real options from the notes.
            if len(options) != 4:
                continue

            rotation = len(questions) % 4
            options = options[rotation:] + options[:rotation]

            correct_index = next(
                i for i, option in enumerate(options)
                if option.lower() == answer_key
            )

            questions.append({
                "text": blanked,
                "options": options,
                "correct_index": correct_index,
                "page": item["page"]
            })

            used_answers.add(answer_key)
            used_statements.add(blanked.lower())
            break

    return questions
