from app.rag.answer_validation import (
    arithmetic_is_consistent,
    citation_errors,
    verify_generated_answer,
)


def test_arithmetic_verification_accepts_correct_equations():
    assert arithmetic_is_consistent(
        "Average speed = 2 * 40 * 60 / (40 + 60) = 48."
    )
    assert arithmetic_is_consistent("0.5 is 2.5 times 0.20.")


def test_arithmetic_verification_rejects_incorrect_equations_and_ratios():
    assert not arithmetic_is_consistent("0.5 / 0.20 = 4.")
    assert not arithmetic_is_consistent("0.5 is four times 0.20.")


def test_citation_validation_requires_actual_source_and_page():
    chunks = [
        {
            "document_name": "Evidence.pdf",
            "page_number": 3,
        }
    ]

    assert citation_errors("Claim [Evidence.pdf, p. 3].", chunks) == []
    assert citation_errors("Claim [Evidence.pdf, p. 4].", chunks)
    assert citation_errors("Claim without a citation.", chunks)


def test_cache_mapping_citations_match_the_retrieved_source_pages():
    chunks = [
        {
            "document_name": "GATE_CSE_2026_FN_Question_Paper.pdf",
            "page_number": 27,
        },
        {
            "document_name": "GATE_CSE_2026_AN_Question_Paper.pdf",
            "page_number": 38,
        },
        {
            "document_name": "Digital_Logic_Memories.pdf",
            "page_number": 18,
        },
        {
            "document_name": "MIT_COA_L07_Memory_Hierarchy.pdf",
            "page_number": 25,
        },
    ]
    answer = (
        "Direct-mapped and set-associative cache appear in the exam passage "
        "[GATE_CSE_2026_FN_Question_Paper.pdf, p. 27]. "
        "A direct-mapped cache problem appears in "
        "[GATE_CSE_2026_AN_Question_Paper.pdf, p. 38]. "
        "The fully associative cache diagram appears in "
        "[MIT_COA_L07_Memory_Hierarchy.pdf, p. 25]."
    )

    assert citation_errors(answer, chunks) == []


def test_answer_verification_combines_citation_and_arithmetic_checks():
    chunks = [{"document_name": "Evidence.pdf", "page_number": 3}]

    verified, errors = verify_generated_answer(
        "2 + 2 = 4 [Evidence.pdf, p. 3].",
        chunks,
    )
    assert verified
    assert errors == []

    verified, errors = verify_generated_answer(
        "0.5 / 0.20 = 4 [Evidence.pdf, p. 3].",
        chunks,
    )
    assert not verified
    assert any("arithmetic" in error.lower() for error in errors)
