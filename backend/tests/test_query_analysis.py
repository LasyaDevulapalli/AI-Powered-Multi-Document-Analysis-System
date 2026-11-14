from app.rag.query_analysis import decompose_question


def test_question_decomposition_retains_full_query_and_explicit_subquestions():
    parts = decompose_question(
        "Compare FCFS and non-preemptive SJF; calculate average waiting time."
    )

    assert parts[0].startswith("Compare FCFS")
    assert any("average waiting time" in item for item in parts)
    assert len(parts) == 3


def test_question_decomposition_does_not_split_comparison_lists():
    parts = decompose_question(
        "Compare direct, fully associative and set-associative cache mapping."
    )

    assert len(parts) == 1


def test_cache_mapping_comparison_decomposes_each_mapping_for_retrieval():
    question = (
        "Explain direct mapping, fully associative mapping, and set-associative "
        "mapping in cache memory. Compare their advantages and disadvantages."
    )

    assert decompose_question(question) == [
        question,
        "direct mapped cache",
        "fully associative cache",
        "set associative cache",
    ]
