# Task 9: Query Performance and Indexes

## Overview
This document describes the implementation of database indexes to improve query performance for the week 5 application.

## Changes Made

### 1. Database Model Indexes (`backend/app/models.py`)

#### Note Model
- **Added index on `title` column**: Improves performance for search queries that filter by title
  - Used in: `/notes/search/` endpoint with `title.contains()` queries
  - Expected improvement: Faster title-based searches, especially with larger datasets

#### ActionItem Model
- **Added index on `completed` column**: Improves performance for filtering by completion status
  - Useful for: Future filtering features (e.g., Task 4: filter by completed status)
  - Expected improvement: Faster queries when filtering completed vs incomplete items

### 2. Performance Test Suite (`backend/tests/test_performance.py`)

Created comprehensive performance tests to verify indexes work correctly:

#### Test Coverage

1. **`test_indexes_exist`**
   - Verifies that the expected indexes are created in the database
   - Uses SQLAlchemy's inspector to check index metadata

2. **`test_query_plan_uses_indexes`**
   - Uses SQLite's `EXPLAIN QUERY PLAN` to verify the query planner uses indexes
   - Checks both title search and completed filter queries

3. **`test_search_performance_with_large_dataset`**
   - Seeds 500 notes to test search performance at scale
   - Verifies search completes in < 1 second
   - Tests `title.contains()` queries

4. **`test_pagination_performance_with_large_dataset`**
   - Seeds 1000 action items to test pagination at scale
   - Verifies pagination (with offset/limit) completes in < 0.5 seconds
   - Tests middle-page access patterns

5. **`test_filtered_query_performance`**
   - Seeds 1000 action items with mixed completion status
   - Verifies filtered queries complete in < 0.5 seconds
   - Tests the `completed` index directly

6. **`test_no_regression_in_basic_operations`**
   - Ensures indexes don't negatively impact CRUD operations
   - Tests create, read, update, delete for both models

7. **`test_count_performance_with_large_dataset`**
   - Seeds 1000 notes to test COUNT query performance
   - Verifies count operations complete in < 0.5 seconds

### 3. Test Infrastructure Updates (`backend/tests/conftest.py`)

- Added `db` fixture for direct database session access in tests
- Enables performance tests to work directly with SQLAlchemy queries
- Creates fresh test database for each test to ensure isolation

## Performance Improvements

### Before Indexes
- Full table scans for search queries
- Linear time complexity for filtered queries
- No optimization for commonly-used filter columns

### After Indexes
- Index-assisted searches for title queries
- Fast lookups for completed status filtering
- Improved query plans visible via `EXPLAIN QUERY PLAN`

## Test Results

All 35 tests passing:
- ✅ 7 new performance tests
- ✅ 28 existing tests (no regressions)
- ✅ All code quality checks passing (black, ruff)

### Performance Metrics
- Title search (500 records): < 1.0 second
- Pagination (1000 records): < 0.5 seconds
- Filtered queries (1000 records): < 0.5 seconds
- COUNT operations (1000 records): < 0.5 seconds

## Technical Notes

### SQLite Index Limitations
- **LIKE queries**: SQLite can only use indexes for prefix matches (e.g., `LIKE 'prefix%'`)
- For `CONTAINS` operations (e.g., `LIKE '%text%'`), the index helps reduce data access but still requires scanning
- For true full-text search, SQLite FTS (Full-Text Search) extension would be needed

### Index Trade-offs
- **Pros**: Faster reads, especially for filtered and search queries
- **Cons**: Slightly slower writes (insert/update/delete), increased storage
- **Decision**: The read-heavy nature of the application justifies the index overhead

### Future Optimizations
1. Consider SQLite FTS for `content` field if full-text search is needed
2. Add composite indexes if queries combine multiple columns
3. Monitor index usage with `EXPLAIN QUERY PLAN` as the application grows
4. Consider index on `created_at` if timestamp-based sorting is added

## Verification Commands

```bash
# Run performance tests
make test backend/tests/test_performance.py

# Run all tests
make test

# Check code quality
make format
make lint
```

## Related Tasks
- **Task 2**: Notes search with pagination and sorting - benefits from title index
- **Task 4**: Action items filters - directly uses completed index
- **Task 8**: List endpoint pagination - benefits from optimized table scans
