from services.qa_service import answer_question, generate_quiz

def sample_note():
    return {
        "pages": [
            {"page_number": 1, "text": (
                "An operating system manages computer hardware and software resources. "
                "Process scheduling selects a process from the ready queue for execution. "
                "Virtual memory allows a computer to execute programs that may not fit entirely in physical memory."
            )}
        ]
    }

def test_answer_returns_source_for_matching_question():
    result = answer_question(sample_note(), "What does process scheduling select?")
    assert result["sources"]
    assert "ready queue" in result["answer"].lower()

def test_unrelated_question_returns_fallback():
    result = answer_question(sample_note(), "What is photosynthesis in plants?")
    assert result["confidence"] == "low"
    assert result["sources"] == []

def test_quiz_is_generated_when_sentences_exist():
    questions = generate_quiz(sample_note(), count=3)
    assert questions
    assert all(len(q["options"]) == 4 for q in questions)
