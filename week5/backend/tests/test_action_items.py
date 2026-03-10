def test_create_and_complete_action_item(client):
    # Test create with success envelope
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    response = r.json()
    assert response["ok"] is True
    assert "data" in response
    item = response["data"]
    assert item["completed"] is False
    assert item["description"] == "Ship it"

    # Test complete with success envelope
    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert "data" in response
    done = response["data"]
    assert done["completed"] is True

    # Test list with success envelope
    r = client.get("/action-items/")
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


def test_action_item_validation_errors(client):
    """Test validation error envelope for empty/invalid action item data"""
    # Empty description
    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert "error" in response
    assert response["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in response["error"]

    # Whitespace-only description
    r = client.post("/action-items/", json={"description": "   "})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Description too long (over 500 characters)
    long_desc = "a" * 501
    r = client.post("/action-items/", json={"description": long_desc})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_action_item_not_found_error(client):
    """Test 404 error envelope for non-existent action item"""
    r = client.put("/action-items/99999/complete")
    assert r.status_code == 404
    response = r.json()
    assert response["ok"] is False
    assert "error" in response
    assert response["error"]["code"] == "NOT_FOUND"
    assert "not found" in response["error"]["message"].lower()


def test_action_items_pagination(client):
    # Create 12 action items
    for i in range(12):
        client.post("/action-items/", json={"description": f"Task {i}"})

    # Test first page
    r = client.get("/action-items/", params={"page": 1, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert data["total"] >= 12

    # Test second page
    r = client.get("/action-items/", params={"page": 2, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 2
    assert len(data["items"]) >= 2

    # Test empty page beyond results
    r = client.get("/action-items/", params={"page": 50, "page_size": 10})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert data["page"] == 50
    assert len(data["items"]) == 0


def test_action_items_pagination_edge_cases(client):
    """Test pagination with edge case parameters"""
    # Create some action items
    for i in range(5):
        client.post("/action-items/", json={"description": f"Task {i}"})

    # Test with page 0
    r = client.get("/action-items/", params={"page": 0, "page_size": 10})
    assert r.status_code == 200

    # Test with negative page
    r = client.get("/action-items/", params={"page": -1, "page_size": 10})
    assert r.status_code == 200

    # Test with zero page size
    r = client.get("/action-items/", params={"page": 1, "page_size": 0})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    assert len(response["data"]["items"]) == 0

    # Test with small page_size
    r = client.get("/action-items/", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    response = r.json()
    assert response["ok"] is True
    data = response["data"]
    assert len(data["items"]) <= 2


def test_action_items_missing_fields(client):
    """Test creating action items with missing required fields"""
    # Missing description
    r = client.post("/action-items/", json={})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Null description
    r = client.post("/action-items/", json={"description": None})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_action_items_invalid_data_types(client):
    """Test creating action items with invalid data types"""
    # Description as number
    r = client.post("/action-items/", json={"description": 12345})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Description as boolean
    r = client.post("/action-items/", json={"description": False})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Description as list
    r = client.post("/action-items/", json={"description": ["task1", "task2"]})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"

    # Description as object
    r = client.post("/action-items/", json={"description": {"text": "task"}})
    assert r.status_code == 422
    response = r.json()
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_action_items_database_consistency(client):
    """Test that database maintains consistency for action items"""
    # Create an action item
    r = client.post("/action-items/", json={"description": "Important Task"})
    assert r.status_code == 201
    item_id = r.json()["data"]["id"]
    assert r.json()["data"]["completed"] is False

    # Complete the action item
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    assert r.json()["data"]["completed"] is True

    # Verify item appears in list with completed status
    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    matching_item = next((item for item in items if item["id"] == item_id), None)
    assert matching_item is not None
    assert matching_item["completed"] is True
    assert matching_item["description"] == "Important Task"


def test_action_items_complete_idempotency(client):
    """Test that completing an already completed item is idempotent"""
    # Create and complete an action item
    r = client.post("/action-items/", json={"description": "Test Task"})
    item_id = r.json()["data"]["id"]

    # Complete it first time
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    assert r.json()["data"]["completed"] is True

    # Complete it again (should be idempotent)
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    assert r.json()["data"]["completed"] is True


def test_action_items_multiple_items(client):
    """Test handling multiple action items correctly"""
    # Create multiple action items
    descriptions = ["Task 1", "Task 2", "Task 3", "Task 4", "Task 5"]
    created_ids = []

    for desc in descriptions:
        r = client.post("/action-items/", json={"description": desc})
        assert r.status_code == 201
        created_ids.append(r.json()["data"]["id"])

    # Complete some of them
    for i in [0, 2, 4]:  # Complete items at indices 0, 2, 4
        r = client.put(f"/action-items/{created_ids[i]}/complete")
        assert r.status_code == 200

    # Verify the list shows correct completion status
    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()["data"]["items"]

    for i, item_id in enumerate(created_ids):
        matching_item = next((item for item in items if item["id"] == item_id), None)
        assert matching_item is not None
        if i in [0, 2, 4]:
            assert matching_item["completed"] is True
        else:
            assert matching_item["completed"] is False
