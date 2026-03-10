def test_create_and_list_notes(client):
    # Test create with success envelope
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    response = r.json()
    assert response["ok"] is True
    assert "data" in response
    assert response["data"]["title"] == "Test"
    assert response["data"]["content"] == "Hello world"

    # Test list with success envelope
    r = client.get("/notes/")
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert "data" in response
    data = response["data"]
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["items"]) >= 1

    # Test search without query
    r = client.get("/notes/search/")
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True

    # Test search with query
    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert len(response["data"]) >= 1


def test_note_validation_errors(client):
    """Test validation error envelope for empty/invalid note data"""
    # Empty title
    r = client.post("/notes/", json={"title": "", "content": "Test"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert "error" in response
    assert response["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in response["error"]

    # Whitespace-only title
    r = client.post("/notes/", json={"title": "   ", "content": "Test"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Empty content
    r = client.post("/notes/", json={"title": "Test", "content": ""})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Title too long (over 200 characters)
    long_title = "a" * 201
    r = client.post("/notes/", json={"title": long_title, "content": "Test"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_note_not_found_error(client):
    """Test 404 error envelope for non-existent note"""
    r = client.get("/notes/99999")
    assert r.status_code == 404
    response = r.json()
    assert response["ok"] is False
    assert "error" in response
    assert response["error"]["code"] == "NOT_FOUND"
    assert "not found" in response["error"]["message"].lower()


def test_extract_from_note_without_apply(client):
    """Test extraction endpoint without persisting data"""
    # Create a note with hashtags and action items
    note_content = """
    Project planning for #python and #fastapi
    
    - [ ] Set up development environment
    - [ ] Write API documentation
    - Ship it!
    
    Using #pytest for testing
    """.strip()

    r = client.post("/notes/", json={"title": "Project Plan", "content": note_content})
    assert r.status_code == 201
    note_id = r.json()["data"]["id"]

    # Extract without applying
    r = client.post(f"/notes/{note_id}/extract", params={"apply": False})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True

    data = response["data"]
    assert "hashtags" in data
    assert "action_items" in data

    # Verify hashtags
    assert "python" in data["hashtags"]
    assert "fastapi" in data["hashtags"]
    assert "pytest" in data["hashtags"]

    # Verify action items
    assert "Set up development environment" in data["action_items"]
    assert "Write API documentation" in data["action_items"]
    assert "Ship it!" in data["action_items"]


def test_extract_from_note_with_apply(client):
    """Test extraction endpoint with persistence"""
    # Create a note
    note_content = """
    Tasks for #backend development:
    - [ ] Implement user authentication
    - [ ] Add rate limiting
    """.strip()

    r = client.post("/notes/", json={"title": "Backend Tasks", "content": note_content})
    assert r.status_code == 201
    note_id = r.json()["data"]["id"]

    # Extract with apply=True
    r = client.post(f"/notes/{note_id}/extract", params={"apply": True})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True

    data = response["data"]
    assert "action_items_created" in data
    assert "tags_found" in data

    # Verify action items were created
    assert len(data["action_items_created"]) == 2
    descriptions = [item["description"] for item in data["action_items_created"]]
    assert "Implement user authentication" in descriptions
    assert "Add rate limiting" in descriptions

    # Verify tags were found
    assert "backend" in data["tags_found"]

    # Verify action items are actually in the database
    r = client.get("/action-items/")
    assert r.status_code == 200
    all_items = r.json()["data"]["items"]
    all_descriptions = [item["description"] for item in all_items]
    assert "Implement user authentication" in all_descriptions
    assert "Add rate limiting" in all_descriptions


def test_extract_from_note_apply_avoids_duplicates(client):
    """Test that applying extraction twice doesn't create duplicates"""
    note_content = "- [ ] Unique task for testing"

    r = client.post("/notes/", json={"title": "Test Note", "content": note_content})
    note_id = r.json()["data"]["id"]

    # First extraction with apply
    r = client.post(f"/notes/{note_id}/extract", params={"apply": True})
    assert r.status_code == 200
    first_created = len(r.json()["data"]["action_items_created"])
    assert first_created == 1

    # Second extraction with apply (should not create duplicates)
    r = client.post(f"/notes/{note_id}/extract", params={"apply": True})
    assert r.status_code == 200
    second_created = len(r.json()["data"]["action_items_created"])
    assert second_created == 0  # No new items created


def test_extract_from_nonexistent_note(client):
    """Test extraction from non-existent note returns 404"""
    r = client.post("/notes/99999/extract")
    assert r.status_code == 404
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "NOT_FOUND"


def test_notes_pagination(client):
    # Create 15 notes
    for i in range(15):
        client.post("/notes/", json={"title": f"Note {i}", "content": f"Content {i}"})

    # Test first page
    r = client.get("/notes/", params={"page": 1, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert data["total"] >= 15

    # Test second page
    r = client.get("/notes/", params={"page": 2, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 2
    assert len(data["items"]) >= 5

    # Test empty page beyond results
    r = client.get("/notes/", params={"page": 100, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 100
    assert len(data["items"]) == 0

    # Test large page size
    r = client.get("/notes/", params={"page": 1, "page_size": 1000})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert len(data["items"]) >= 15


def test_notes_pagination_edge_cases(client):
    """Test pagination with edge case parameters"""
    # Create some notes
    for i in range(5):
        client.post("/notes/", json={"title": f"Note {i}", "content": f"Content {i}"})

    # Test with page 0 (should still work, implementation dependent)
    r = client.get("/notes/", params={"page": 0, "page_size": 10})
    assert r.status_code == 200

    # Test with negative page (should still work, calculates negative offset)
    r = client.get("/notes/", params={"page": -1, "page_size": 10})
    assert r.status_code == 200

    # Test with zero page size (edge case)
    r = client.get("/notes/", params={"page": 1, "page_size": 0})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert len(response["data"]["items"]) == 0

    # Test with page 1 and small page_size
    r = client.get("/notes/", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert len(data["items"]) <= 2


def test_notes_search_edge_cases(client):
    """Test search functionality with various edge cases"""
    # Create test notes with specific content
    client.post("/notes/", json={"title": "Python Tutorial", "content": "Learn Python"})
    client.post(
        "/notes/",
        json={"title": "JavaScript Guide", "content": "Learn JavaScript"},
    )
    client.post("/notes/", json={"title": "Special !@#$ Characters", "content": "Testing"})

    # Search with empty query (should return all)
    r = client.get("/notes/search/", params={"q": ""})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    # Empty query should return all notes
    assert len(response["data"]) >= 3

    # Search with special characters
    r = client.get("/notes/search/", params={"q": "!@#$"})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True

    # Search with partial match
    r = client.get("/notes/search/", params={"q": "Pyth"})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert len(response["data"]) >= 1

    # Search with no matches
    r = client.get("/notes/search/", params={"q": "NONEXISTENTQUERY123456"})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert len(response["data"]) == 0

    # Search with very long query
    long_query = "x" * 500
    r = client.get("/notes/search/", params={"q": long_query})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True


def test_notes_missing_fields(client):
    """Test creating notes with missing required fields"""
    # Missing title
    r = client.post("/notes/", json={"content": "Test content"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Missing content
    r = client.post("/notes/", json={"title": "Test title"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Missing both fields
    r = client.post("/notes/", json={})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_notes_invalid_data_types(client):
    """Test creating notes with invalid data types"""
    # Title as number
    r = client.post("/notes/", json={"title": 123, "content": "Test"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Content as boolean
    r = client.post("/notes/", json={"title": "Test", "content": True})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Title as list
    r = client.post("/notes/", json={"title": ["a", "b"], "content": "Test"})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_notes_database_consistency(client):
    """Test that database maintains consistency"""
    # Create a note
    r = client.post("/notes/", json={"title": "Test Note", "content": "Test Content"})
    assert r.status_code == 201
    note_id = r.json()["data"]["id"]

    # Retrieve the note
    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 200
    note = r.json()["data"]
    assert note["title"] == "Test Note"
    assert note["content"] == "Test Content"

    # Verify note appears in list
    r = client.get("/notes/")
    assert r.status_code == 200
    notes = r.json()["data"]["items"]
    assert any(n["id"] == note_id for n in notes)

    # Verify note appears in search
    r = client.get("/notes/search/", params={"q": "Test Note"})
    assert r.status_code == 200
    search_results = r.json()["data"]
    assert any(n["id"] == note_id for n in search_results)
