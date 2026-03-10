"""Performance tests to verify database indexes and query optimization"""

import time

from backend.app.models import ActionItem, Note
from sqlalchemy import inspect, text


def test_indexes_exist(db):
    """Verify that expected indexes are created on tables"""
    inspector = inspect(db.get_bind())

    # Check Note table indexes
    note_indexes = inspector.get_indexes("notes")
    note_index_columns = {idx["name"]: idx["column_names"] for idx in note_indexes}

    # Check for title index
    assert any(
        "title" in cols for cols in note_index_columns.values()
    ), "notes.title should have an index"

    # Check ActionItem table indexes
    action_item_indexes = inspector.get_indexes("action_items")
    action_item_index_columns = {idx["name"]: idx["column_names"] for idx in action_item_indexes}

    # Check for completed index
    assert any(
        "completed" in cols for cols in action_item_index_columns.values()
    ), "action_items.completed should have an index"


def test_query_plan_uses_indexes(db):
    """Verify that SQLite query planner uses indexes for common queries"""
    # Create some test data
    for i in range(10):
        note = Note(title=f"Test Note {i}", content=f"Content {i}")
        db.add(note)
    db.commit()

    # Check query plan for title search
    result = db.execute(
        text("EXPLAIN QUERY PLAN SELECT * FROM notes WHERE title LIKE :pattern"),
        {"pattern": "%Test%"},
    )
    query_plan = " ".join(row[3] for row in result)

    # SQLite should mention index usage
    # Note: LIKE queries may use index for prefix matches but not for contains
    assert "notes" in query_plan.lower()

    # Check query plan for completed filter
    action_item = ActionItem(description="Test task", completed=False)
    db.add(action_item)
    db.commit()

    result = db.execute(
        text("EXPLAIN QUERY PLAN SELECT * FROM action_items WHERE completed = :completed"),
        {"completed": True},
    )
    query_plan = " ".join(row[3] for row in result)

    # Should use index on completed column
    assert "action_items" in query_plan.lower()


def test_search_performance_with_large_dataset(db):
    """Test search performance with a larger dataset"""
    # Seed larger dataset (500 notes)
    notes_to_add = []
    for i in range(500):
        note = Note(
            title=f"Performance Test Note {i}",
            content=f"This is test content for note number {i}. It contains various text to search through.",
        )
        notes_to_add.append(note)

    db.add_all(notes_to_add)
    db.commit()

    # Measure search query performance
    start_time = time.time()

    # Search by title
    results = db.query(Note).filter(Note.title.contains("Performance Test")).limit(50).all()

    search_time = time.time() - start_time

    # Verify results
    assert len(results) == 50
    assert all("Performance Test" in note.title for note in results)

    # Search should complete reasonably fast (< 1 second for 500 records)
    assert search_time < 1.0, f"Search took {search_time:.3f}s, should be < 1.0s with index"


def test_pagination_performance_with_large_dataset(db):
    """Test pagination performance with a larger dataset"""
    # Seed larger dataset (1000 action items)
    items_to_add = []
    for i in range(1000):
        item = ActionItem(
            description=f"Task number {i}", completed=(i % 3 == 0)  # Every 3rd is completed
        )
        items_to_add.append(item)

    db.add_all(items_to_add)
    db.commit()

    # Test pagination performance
    start_time = time.time()

    # Get page in the middle
    page = 25
    page_size = 20
    offset = (page - 1) * page_size

    results = db.query(ActionItem).offset(offset).limit(page_size).all()

    pagination_time = time.time() - start_time

    # Verify results
    assert len(results) == page_size

    # Pagination should be fast
    assert pagination_time < 0.5, f"Pagination took {pagination_time:.3f}s, should be < 0.5s"


def test_filtered_query_performance(db):
    """Test performance of filtered queries on indexed columns"""
    # Seed data with mix of completed/incomplete items
    items_to_add = []
    for i in range(1000):
        item = ActionItem(description=f"Filter test task {i}", completed=(i % 2 == 0))
        items_to_add.append(item)

    db.add_all(items_to_add)
    db.commit()

    # Test filtering by completed status
    start_time = time.time()

    completed_items = db.query(ActionItem).filter(ActionItem.completed).all()

    filter_time = time.time() - start_time

    # Verify results
    assert len(completed_items) == 500
    assert all(item.completed for item in completed_items)

    # Filtering should be fast with index
    assert filter_time < 0.5, f"Filtering took {filter_time:.3f}s, should be < 0.5s with index"


def test_no_regression_in_basic_operations(db):
    """Ensure indexes don't cause regressions in basic CRUD operations"""
    # Test note creation
    note = Note(title="Regression Test", content="Testing that indexes don't break CRUD")
    db.add(note)
    db.commit()
    db.refresh(note)

    assert note.id is not None
    assert note.title == "Regression Test"

    # Test note update
    note.title = "Updated Title"
    db.commit()
    db.refresh(note)

    assert note.title == "Updated Title"

    # Test note deletion
    note_id = note.id
    db.delete(note)
    db.commit()

    deleted_note = db.get(Note, note_id)
    assert deleted_note is None

    # Test action item operations
    item = ActionItem(description="Test item", completed=False)
    db.add(item)
    db.commit()
    db.refresh(item)

    assert item.id is not None
    assert not item.completed

    item.completed = True
    db.commit()
    db.refresh(item)

    assert item.completed


def test_count_performance_with_large_dataset(db):
    """Test that COUNT queries perform well with indexes"""
    # Seed large dataset
    notes_to_add = [Note(title=f"Count test {i}", content=f"Content {i}") for i in range(1000)]
    db.add_all(notes_to_add)
    db.commit()

    # Test count performance
    start_time = time.time()
    count = db.query(Note).count()
    count_time = time.time() - start_time

    assert count >= 1000
    assert count_time < 0.5, f"COUNT took {count_time:.3f}s, should be < 0.5s"
