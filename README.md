# Sales Leads Tracker

A small FastAPI app for tracking sales leads. Add a lead (name, company, region,
status), list all leads, and filter by status — from a web page or a JSON API.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/uvicorn app.main:app --reload
```

- Web UI: http://127.0.0.1:8000/
- API docs (Swagger): http://127.0.0.1:8000/docs

Data is stored in `leads.db` (SQLite) in the project root, created on first run.

## Test

```bash
.venv/bin/pytest -v
```

Tests run against an in-memory database and never touch `leads.db`.

## API

| Method | Path                       | Description                          |
|--------|----------------------------|--------------------------------------|
| POST   | `/api/leads`               | Create a lead (201)                  |
| GET    | `/api/leads`               | List leads, newest first             |
| GET    | `/api/leads?status=won`    | List leads with a given status       |
| GET    | `/api/leads/{id}`          | Get one lead (404 if missing)        |

Lead body:

```json
{ "name": "Ada Lovelace", "company": "Acme", "region": "EMEA", "status": "qualified" }
```

`status` is one of `new`, `contacted`, `qualified`, `won`, `lost` and defaults to
`new`. Invalid or blank fields return a 422.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","company":"Acme","region":"EMEA","status":"qualified"}'

curl "http://127.0.0.1:8000/api/leads?status=qualified"
```

## Project layout

```
app/
  main.py          FastAPI app: JSON API + HTML routes
  database.py      SQLite engine, session factory, get_db dependency
  models.py        SQLAlchemy Lead table
  schemas.py       Pydantic models and Status enum
  templates/
    index.html     Web UI (add form, status filter, leads table)
tests/
  conftest.py      TestClient fixture backed by an in-memory DB
  test_leads.py    JSON API tests
  test_html.py     HTML UI tests
```
