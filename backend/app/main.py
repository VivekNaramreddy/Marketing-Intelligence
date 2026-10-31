from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from . import models
from .findings import generate_findings
from .metrics import analyze
from .normalization import normalize, read_file
from .reports import build_report
from .storage import Base, engine, session

Base.metadata.create_all(engine)
app = FastAPI(title='Marketing Intelligence', version='0.1.0')
DB = Annotated[DBSession, Depends(session)]


class WorkspaceInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class Selection(BaseModel):
    primary_brand: str
    competitors: list[str]


class ManualInput(BaseModel):
    rows: list[dict]


def workspace(db, workspace_id):
    value = db.get(models.Workspace, workspace_id)
    if not value:
        raise HTTPException(404, 'Workspace not found.')
    return value


def records(db, workspace_id):
    observations = db.scalars(select(models.Observation).where(models.Observation.workspace_id == workspace_id)).all()
    batches = {b.id: b for b in db.scalars(select(models.ImportBatch).where(models.ImportBatch.workspace_id == workspace_id))}
    return [{**{c.name: getattr(r, c.name) for c in models.Observation.__table__.columns}, 'source': batches[r.import_id].filename, 'imported_at': batches[r.import_id].created_at} for r in observations]


def import_rows(db, workspace_id, filename, raw):
    workspace(db, workspace_id)
    try:
        normalized = normalize(raw)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    batch = models.ImportBatch(workspace_id=workspace_id, filename=filename, raw_rows=raw)
    db.add(batch)
    db.flush()
    for index, row in enumerate(normalized, 2):
        db.add(models.Observation(workspace_id=workspace_id, import_id=batch.id, source_row=index, **row))
    db.commit()
    return {'import_id': batch.id, 'count': len(normalized)}


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/workspaces')
def list_workspaces(db: DB):
    return db.scalars(select(models.Workspace).order_by(models.Workspace.id)).all()


@app.post('/api/workspaces', status_code=201)
def create_workspace(body: WorkspaceInput, db: DB):
    if not body.name.strip():
        raise HTTPException(422, 'Workspace name is required.')
    value = models.Workspace(name=body.name.strip(), competitors=[])
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@app.put('/api/workspaces/{workspace_id}/selection')
def select_brands(workspace_id: int, body: Selection, db: DB):
    value = workspace(db, workspace_id)
    brands = {r['brand'] for r in records(db, workspace_id)}
    if body.primary_brand not in brands or any(b not in brands or b == body.primary_brand for b in body.competitors):
        raise HTTPException(422, 'Select imported brands; the primary brand cannot also be a competitor.')
    value.primary_brand = body.primary_brand
    value.competitors = list(dict.fromkeys(body.competitors))
    db.commit()
    return {'ok': True}


@app.get('/api/workspaces/{workspace_id}/data')
def get_data(workspace_id: int, db: DB):
    workspace(db, workspace_id)
    rows = records(db, workspace_id)
    return {'rows': rows, 'brands': sorted({r['brand'] for r in rows}), 'imports': [{'id': b.id, 'filename': b.filename, 'created_at': b.created_at, 'count': len(b.raw_rows)} for b in db.scalars(select(models.ImportBatch).where(models.ImportBatch.workspace_id == workspace_id))]}


@app.get('/api/workspaces/{workspace_id}/imports/{import_id}')
def raw_import(workspace_id: int, import_id: int, db: DB):
    value = db.get(models.ImportBatch, import_id)
    if not value or value.workspace_id != workspace_id:
        raise HTTPException(404, 'Import not found.')
    return {'filename': value.filename, 'rows': value.raw_rows}


@app.post('/api/workspaces/{workspace_id}/import')
async def upload(workspace_id: int, db: DB, file: UploadFile = File(...)):
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, 'Files must be 5 MB or smaller.')
    try:
        rows = read_file(file.filename or '', content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return import_rows(db, workspace_id, file.filename, rows)


@app.post('/api/workspaces/{workspace_id}/manual')
def manual(workspace_id: int, body: ManualInput, db: DB):
    return import_rows(db, workspace_id, 'Manual entry', body.rows)


@app.post('/api/workspaces/{workspace_id}/demo')
def demo(workspace_id: int, db: DB):
    value = workspace(db, workspace_id)
    filename = 'DEMO_fictional_social.csv'
    existing = db.scalar(select(models.ImportBatch).where(models.ImportBatch.workspace_id == workspace_id, models.ImportBatch.filename == filename))
    if existing:
        raise HTTPException(409, 'Demo data is already loaded in this workspace.')
    rows = read_file(filename, (Path(__file__).resolve().parents[1] / 'demo' / filename).read_bytes())
    result = import_rows(db, workspace_id, filename, rows)
    value.primary_brand = 'New Haven Symphony Orchestra'
    value.competitors = sorted({r['Brand'] for r in rows if r['Brand'] != value.primary_brand})
    db.commit()
    return result


def intelligence(workspace_id, db):
    value = workspace(db, workspace_id)
    if not value.primary_brand:
        raise HTTPException(422, 'Choose a primary brand on the Data page to begin.')
    metrics = analyze(records(db, workspace_id), value.primary_brand, value.competitors or [])
    return value, metrics, generate_findings(metrics)


@app.get('/api/workspaces/{workspace_id}/analysis')
def get_analysis(workspace_id: int, db: DB):
    value, metrics, findings = intelligence(workspace_id, db)
    return {'primary_brand': value.primary_brand, 'metrics': metrics, 'findings': findings}


@app.post('/api/workspaces/{workspace_id}/report')
def report(workspace_id: int, db: DB):
    value, metrics, findings = intelligence(workspace_id, db)
    return build_report(value.primary_brand, metrics, findings)
