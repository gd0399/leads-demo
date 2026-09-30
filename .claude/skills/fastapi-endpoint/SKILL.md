fastapi-endpoint
dd or modify an endpoint in a FastAPI project following Tror's layered conventions. Use when the user asks to add, change, or remove an API route, endpoint, or resource — for example "add an endpoint to update a lead", "let users delete a lead", "add a search endpoint", "add pagination to the list route". Covers the schema, model, route, and test changes together so no layer is left out.
mkdir -p ~/leads-demo/.claude/skills/fastapi-endpoint && cat > ~/leads-demo/.claude/skills/fastapi-endpoint/SKILL.md <<'EOF'
---
name: fastapi-endpoint
description: Add or modify an endpoint in a FastAPI project following Tror's layered conventions. Use when the user asks to add, change, or remove an API route, endpoint, or resource — for example "add an endpoint to update a lead", "let users delete a lead", "add a search endpoint", "add pagination to the list route". Covers the schema, model, route, and test changes together so no layer is left out.
---

# FastAPI endpoint (house style)

Follow this pattern for every endpoint change, so endpoints written by
different people — or by an agent — come out the same shape.

## Before writing anything

1. Read the existing route file and one nearby endpoint. Match its style.
2. State what you will change in each layer, and ask the user to confirm
   anything ambiguous (field names, status codes, destructive changes).
3. Never modify more than the endpoint asked for.

## The layers, in order

### 1. Schemas (app/schemas.py)
- Input goes in a Pydantic model, never a raw dict or loose query params.
- Every string field gets min_length=1 and a sensible max_length.
- A field with a fixed set of values gets an Enum, never a free string.
- Response models are separate from request models; reuse what exists.

### 2. Models (app/models.py)
- Change only if a new column is genuinely needed.
- Columns are nullable=False unless truly optional.
- Enum columns share the same Python enum the schema uses.
- If a column is added, say so explicitly: SQLite will not add it to an
  existing database, so the user must delete the local file or migrate.

### 3. Route (app/main.py)
- Filtering, searching and sorting happen in the database query, never by
  loading every row and filtering in Python.
- Reuse the shared query helper rather than rewriting the filter.
- Take the database session through the existing dependency.
- Status codes: 201 create, 200 read/update, 204 delete, 404 missing,
  422 invalid input.
- Flag destructive routes to the user before finishing.

### 4. Tests (tests/)
Cover the success path AND the failure paths, at minimum:
- Happy path returns the expected status code and body.
- Invalid input returns 422.
- A missing record returns 404.
- Filters and searches return only matching rows, and nothing when none match.
- An operation on one record leaves the others untouched.
Use the existing fixtures and the in-memory database only.

## Finish by

1. Running the full test suite and reporting the actual output — the real
   number passing and failing, not a claim that it works.
2. Summarising what changed, file by file.
3. Naming anything the user must do by hand.
4. Updating README.md when routes change.

Do not commit or push. The user reviews first.
