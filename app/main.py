from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import Lead
from app.schemas import LeadCreate, LeadOut, Status

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Sales Leads Tracker", lifespan=lifespan)


def query_leads(db: Session, status: Status | None) -> list[Lead]:
    query = db.query(Lead)
    if status is not None:
        query = query.filter(Lead.status == status)
    return query.order_by(Lead.created_at.desc(), Lead.id.desc()).all()


# --- JSON API ---------------------------------------------------------------


@app.post("/api/leads", response_model=LeadOut, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> Lead:
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads(
    status: Status | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Lead]:
    return query_leads(db, status)


@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# --- HTML UI ----------------------------------------------------------------


def render_index(
    request: Request,
    db: Session,
    status: Status | None,
    *,
    form: dict | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "leads": query_leads(db, status),
            "statuses": list(Status),
            "status_filter": status,
            "form": form or {"name": "", "company": "", "region": "", "status": Status.new.value},
            "error": error,
        },
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    status: Status | None = Query(default=None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return render_index(request, db, status)


@app.post("/leads")
def create_lead_form(
    request: Request,
    name: str = Form(""),
    company: str = Form(""),
    region: str = Form(""),
    status: str = Form(Status.new.value),
    db: Session = Depends(get_db),
):
    form = {"name": name.strip(), "company": company.strip(), "region": region.strip(), "status": status}
    try:
        payload = LeadCreate(**form)
    except ValidationError as exc:
        first = exc.errors()[0]
        message = f"{first['loc'][0]}: {first['msg']}"
        return render_index(request, db, None, form=form, error=message, status_code=422)

    db.add(Lead(**payload.model_dump()))
    db.commit()
    return RedirectResponse(url="/", status_code=303)
