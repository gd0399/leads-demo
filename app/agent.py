import json
import sys

import anthropic
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Lead

SYSTEM = (
    "You turn a plain-English question about sales leads into a search filter.\n"
    "Valid statuses: new, contacted, qualified, won, lost\n"
    "Reply with ONLY a JSON object, no markdown fences and no explanation:\n"
    '{"status": <one status or null>, "company": <text or null>, "region": <text or null>}\n'
    "Use null for anything the question does not mention.\n"
    "Examples:\n"
    'qualified leads in the south -> {"status": "qualified", "company": null, "region": "south"}\n'
    'anything from acme -> {"status": null, "company": "acme", "region": null}\n'
    'who have we won -> {"status": "won", "company": null, "region": null}'
)


def parse_question(question):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM,
        messages=[{"role": "user", "content": question}],
    )
    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def search(filters):
    db = SessionLocal()
    try:
        query = db.query(Lead)
        if filters.get("status"):
            query = query.filter(Lead.status == filters["status"])
        if filters.get("company"):
            query = query.filter(func.lower(Lead.company).contains(filters["company"].lower()))
        if filters.get("region"):
            query = query.filter(func.lower(Lead.region).contains(filters["region"].lower()))
        return query.order_by(Lead.id.desc()).all()
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print('Usage: .venv/bin/python -m app.agent "your question"')
        return
    question = " ".join(sys.argv[1:])
    filters = parse_question(question)
    print("")
    print("Question: " + question)
    print("Filter:   " + json.dumps(filters))
    print("")
    leads = search(filters)
    if not leads:
        print("No leads match that.")
        return
    for lead in leads:
        print("  " + lead.name + " - " + lead.company + " (" + lead.region + ") - " + lead.status.value)
    print("")
    print(str(len(leads)) + " lead(s) found.")


if __name__ == "__main__":
    main()
