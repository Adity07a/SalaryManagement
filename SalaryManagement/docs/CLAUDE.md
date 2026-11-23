
#  Salary Management — Project Instructions

## 1. Project Principles

- Prioritize correctness, readability, and maintainability.
- Prefer simple solutions over unnecessary abstractions.
- Do not introduce speculative features.
- Preserve existing functionality when modifying code.
- Do not create dead code, unused dependencies, or TODO placeholders.
- Explain non-obvious engineering decisions briefly.

## 2. Technology Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL 15+
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- pytest and httpx

### Frontend
- React
- Vite
- TypeScript
- Material UI
- TanStack Query
- Recharts
- Vitest
- React Testing Library

Do not substitute the specified technology stack without approval.

## 3. Backend Architecture

Follow this architecture:

Routes -> Services -> Repositories -> Database

Rules:
- Routes must remain thin.
- Business logic belongs in services.
- Database operations belong in repositories.
- Pydantic schemas handle request and response validation.
- Statistical functions must not depend on database sessions.
- Use dependency injection for database sessions.

## 4. Monetary and Salary Rules

- Always use Python Decimal for monetary calculations.
- Use PostgreSQL NUMERIC for stored monetary values.
- Never use floating-point values for salary calculations.
- Salary amounts represent annual gross compensation.
- Salary amounts are stored in the employee's local currency.
- USD is the base currency for international comparisons.
- Never average or aggregate different local currencies directly.
- Convert values using the exchange_rates table before comparisons.
- Never overwrite historical salary records.
- Salary changes must insert new salary records.
- The current salary is the record with the latest effective_from date.

## 5. Database Rules

- Use SQLAlchemy 2.x.
- Use Alembic for schema migrations.
- Keep database queries inside repositories.
- Apply filtering, sorting, grouping, pagination, and percentile calculations in PostgreSQL.
- Never load all 10,000 employee records into Python for analytics.
- Never send the full employee dataset to the frontend.
- Add indexes for frequently queried columns.
- Use database constraints to protect data integrity.

## 6. API Rules

- All application endpoints must use /api/v1.
- Use meaningful HTTP status codes.
- Maintain a consistent error response structure:

  {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable error message",
      "details": {}
    }
  }

- Handle missing records, duplicate emails, and validation errors.
- Validate data at API boundaries.
- Include the /health endpoint.

## 7. Testing Rules

- Write tests together with the feature being implemented.
- Keep tests deterministic and independent.
- Use fixed random seeds.
- Do not depend on network access.
- Do not use sleeps in tests.
- Prefer unit tests for business logic.
- Use a separate PostgreSQL test database for API tests.
- Test important failure cases, not just successful responses.
- Do not chase 100% code coverage.

## 8. Seed Data Rules

- Use Faker with a fixed seed.
- Generate exactly 10,000 employees.
- Use bulk inserts or other efficient database insertion methods.
- The seed script must be safe to rerun.
- Generate realistic salary distributions and deliberate outliers.
- Verify reproducibility with automated tests.

## 9. Frontend Rules

- Use TypeScript.
- Keep API communication inside the typed API client.
- Use TanStack Query for server state.
- Use MUI components for tables and forms.
- Use Recharts for analytics visualizations.
- Implement loading, error, and empty states.
- Use debounce for employee search.
- Validate form values before submission.
- Display local salary and USD equivalent clearly.

## 10. Git and Development Workflow

- Follow the provided 17-step commit plan in order.
- Work in small vertical slices.
- Complete and test one slice before starting another.
- Do not proceed to the next step without explicit approval.
- Use Conventional Commits.
- Keep commit subjects under 72 characters.
- Use imperative present tense in commit messages.
- Never commit secrets, .env files, or build artifacts.
- Commit .env.example instead of actual environment files.

## 11. AI Collaboration Rules

- Explain the intended changes before each implementation slice.
- Identify the exact files that will be modified.
- Write tests alongside implementation.
- Run relevant tests and report actual results.
- Show important implementation decisions for review.
- Record useful prompts and AI mistakes in docs/ai-usage.md.
- Do not silently change architecture or requirements.
