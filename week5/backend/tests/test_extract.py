from backend.app.services.extract import (
    extract_action_items,
    extract_all,
    extract_hashtags,
)


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "Ship it!" in items


def test_extract_action_items_markdown_checkboxes():
    """Test extraction of markdown checkbox format"""
    text = """
    # My Tasks
    - [ ] Write documentation
    - [x] Complete feature
    - [ ] Review PR
    Regular text
    """.strip()
    items = extract_action_items(text)
    assert "Write documentation" in items
    assert "Complete feature" in items
    assert "Review PR" in items
    assert len(items) == 3


def test_extract_hashtags():
    """Test extraction of hashtags"""
    text = """
    This is a note about #python and #testing.
    #API development with #FastAPI.
    Duplicate #python tag should appear once.
    """.strip()
    tags = extract_hashtags(text)
    assert "python" in tags
    assert "testing" in tags
    assert "api" in tags
    assert "fastapi" in tags
    # Check uniqueness (python appears twice but should be in list once)
    assert tags.count("python") == 1


def test_extract_hashtags_edge_cases():
    """Test hashtag extraction edge cases"""
    # Test with numbers and underscores
    text = "#bug_fix #python3 #test_123"
    tags = extract_hashtags(text)
    assert "bug_fix" in tags
    assert "python3" in tags
    assert "test_123" in tags

    # Test empty text
    assert extract_hashtags("") == []

    # Test text without hashtags
    assert extract_hashtags("Just plain text") == []


def test_extract_all():
    """Test combined extraction of hashtags and action items"""
    text = """
    Project notes for #python #webdev
    
    - [ ] Implement authentication
    - [ ] Add tests for #API endpoints
    - Ship it!
    
    More notes about #fastapi
    """.strip()
    result = extract_all(text)

    # Check hashtags
    assert "python" in result["hashtags"]
    assert "webdev" in result["hashtags"]
    assert "api" in result["hashtags"]
    assert "fastapi" in result["hashtags"]

    # Check action items
    assert "Implement authentication" in result["action_items"]
    assert "Add tests for #API endpoints" in result["action_items"]
    assert "Ship it!" in result["action_items"]
