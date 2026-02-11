import pytest
from ollama import list as ollama_list

from ..app.services.extract import extract_action_items, extract_action_items_llm

# ── extract_action_items (기존 heuristic) ──

def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ── extract_action_items_llm (실제 모델 사용) ──

def _ollama_has_model(model_name: str) -> bool:
    """로컬 Ollama에 해당 모델이 있는지 확인한다."""
    try:
        models = ollama_list()
        return any(model_name in m.model for m in models.models)
    except Exception:
        return False


# MODELS = ["deepseek-r1:1.5b"]
MODELS = ["llama3.1:8b"]


@pytest.fixture(params=[m for m in MODELS if _ollama_has_model(m)])
def model_name(request):
    return request.param


def test_llm_bullet_list(model_name):
    result = extract_action_items_llm(
        "- buy milk\n- call john\n- pick up dry cleaning",
        model=model_name,
    )
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, str) for item in result)


def test_llm_keyword_prefixed_lines(model_name):
    result = extract_action_items_llm(
        "todo: finish the report\naction: review PR #42",
        model=model_name,
    )
    assert isinstance(result, list)
    assert len(result) > 0


def test_llm_empty_input(model_name):
    result = extract_action_items_llm("", model=model_name)
    assert isinstance(result, list)
    assert len(result) == 0


def test_llm_no_action_items_in_text(model_name):
    result = extract_action_items_llm(
        "The weather is nice today. I had a good lunch.",
        model=model_name,
    )
    assert isinstance(result, list)
    assert len(result) == 0
