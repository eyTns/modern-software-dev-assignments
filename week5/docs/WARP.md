# Warp Automation Rules
When receiving a task request, analyze the task type and execute the appropriate workflow.



## Test Runner with Coverage and Flaky-Test Re-run

### Workflow
1. Run tests with coverage and retry
   ```bash
   make test-coverage
   ```
   Command: `pytest backend/tests --cov=backend --cov-report=html --cov-report=term --reruns 2`

2. Analyze coverage report
   - Parse terminal output for coverage percentages
   - Parse `htmlcov/index.html` for line-by-line coverage data
   - Identify files below coverage targets

3. Generate missing tests automatically
   - For each uncovered line, analyze the code context
   - Generate appropriate test cases to cover those lines
   - Add tests to existing test files or create new ones
   - Ensure tests follow existing test patterns in the codebase

4. Re-run tests with coverage
   ```bash
   make test-coverage
   ```

### Coverage Targets
- Core business logic (services, routers): 90% or higher
- Other code (db, models, utils): 80% or higher



## API Documentation Sync

### Workflow
1. Fetch current OpenAPI spec
   ```bash
   curl http://localhost:8000/openapi.json > docs/openapi.json
   ```

2. Generate markdown documentation from OpenAPI spec
   - Parse `docs/openapi.json`
   - Convert to readable markdown format with endpoint descriptions, parameters, and responses
   - Save to `docs/API.md`

3. Compare with previous version
   - Load previous `docs/API.md` if it exists
   - Identify added endpoints
   - Identify removed endpoints
   - Identify changed parameters or response schemas
   - Generate a delta report

4. Update `docs/API.md` with new content and show delta report

### Output Format
- Show route deltas (added/removed/modified endpoints)
- Include parameter changes
- Include response schema changes

## Refactor Harness: Module Rename

### Workflow
1. Rename the module file
   - Move/rename the target file

2. Update all imports automatically
   - Search codebase for all files importing the renamed module
   - Update import statements to use new module name
   - Update any string references to the module path

3. Run lint
   ```bash
   make lint
   ```

4. Run tests
   ```bash
   make test
   ```

5. Report results
   - List all files that were updated
   - Show lint results
   - Show test results
   - If any failures, automatically roll back all changes

## Release Helper

### Workflow
1. Bump version number
   - Update version in `pyproject.toml`
   - Specify version type: major, minor, or patch

2. Run quality checks
   ```bash
   make lint
   make test
   ```

3. Generate changelog snippet automatically
   - Analyze git commits since last release tag
   - Categorize changes by commit message patterns (feat:, fix:, breaking:)
   - Format as markdown with proper sections

4. Prepare release summary
   - Show new version number
   - Show lint and test results
   - Show generated changelog snippet
   - If checks fail, abort release
