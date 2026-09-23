import asyncio
import csv
import hashlib
import json
from contextlib import asynccontextmanager
from datetime import date
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select, delete
from .models import Base, engine, SessionLocal, User, Category, Transaction, InsightCache
from .schemas import CATEGORIES, ChatRequest, Insight
from .csv_service import parse_csv
from .analytics import dashboard, month_bounds
from .demo import demo_csv
from . import ai_service

mutation_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.get(User, 1):
            db.add(User(id=1))
        for i, name in enumerate(CATEGORIES, 1):
            if not db.get(Category, i):
                db.add(Category(id=i, name=name))
        db.commit()
    yield

app = FastAPI(title='Теңге · Финансовый ассистент', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'], allow_methods=['GET', 'POST'], allow_headers=['*'])

@app.get('/api/health')
def health():
    return {'status': 'ok'}

async def save_rows(rows, use_ai=True):
    async with mutation_lock:
        with SessionLocal() as db:
            existing = {(r.date, r.description, r.amount_minor, r.kind) for r in db.scalars(select(Transaction))}
            # Повторная загрузка не дублирует операции; одинаковые строки внутри одного CSV сохраняются.
            fresh = [Transaction(**r) for r in rows if (r['date'], r['description'], r['amount_minor'], r['kind']) not in existing]
            db.add_all(fresh)
            db.flush()
            expenses = [r for r in fresh if r.kind == 'expense']
            warnings = []
            if use_ai:
                warnings = await ai_service.categorize(expenses)
            else:
                for r in expenses:
                    r.category_id = CATEGORIES.index(ai_service.local_category(r.description)) + 1
                    r.source = 'local'
            for r in fresh:
                if r.kind == 'income':
                    r.source = 'income'
            db.execute(delete(InsightCache))
            db.commit()
            return {'imported': len(fresh), 'skipped': len(rows) - len(fresh), 'warnings': warnings}

@app.post('/api/upload')
async def upload(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(422, 'Выберите файл с расширением .csv.')
    raw = await file.read(2 * 1024 * 1024 + 1)
    await file.close()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(413, 'Файл больше 2 МБ. Разделите его на несколько файлов.')
    try:
        rows = parse_csv(raw)
    except (ValueError, csv.Error) as exc:
        raise HTTPException(422, str(exc)) from exc
    return await save_rows(rows)

@app.post('/api/demo')
async def demo():
    return await save_rows(parse_csv(demo_csv()), use_ai=False)

@app.get('/api/demo.csv')
def download_demo():
    return Response(demo_csv(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="demo-transactions.csv"'})

@app.post('/api/categorize')
async def recategorize():
    async with mutation_lock:
        with SessionLocal() as db:
            rows = list(db.scalars(select(Transaction).where(Transaction.kind == 'expense', Transaction.source != 'claude')))
            warnings = await ai_service.categorize(rows)
            db.execute(delete(InsightCache))
            db.commit()
            return {'processed': len(rows), 'warnings': warnings}

@app.get('/api/months')
def months():
    with SessionLocal() as db:
        return sorted({d.strftime('%Y-%m') for d in db.scalars(select(Transaction.date))}, reverse=True)

def get_dashboard(month):
    try:
        month_bounds(month)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    with SessionLocal() as db:
        return dashboard(list(db.scalars(select(Transaction))), month)

@app.get('/api/dashboard')
def get_stats(month: str = Query(pattern=r'^\d{4}-\d{2}$')):
    return get_dashboard(month)

@app.post('/api/insights')
async def get_insights(month: str = Query(pattern=r'^\d{4}-\d{2}$'), refresh: bool = False):
    data = get_dashboard(month)
    if not data['count']:
        raise HTTPException(422, 'За этот месяц нет транзакций. Сначала загрузите CSV.')
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:20]
    key = f'{date.today()}:{month}:{fingerprint}'
    async with mutation_lock:
        with SessionLocal() as db:
            cached = db.get(InsightCache, key)
            if cached and not refresh:
                return dict(json.loads(cached.payload), cached=True)
            result = await ai_service.insights(data)
            db.merge(InsightCache(key=key, payload=json.dumps(result, ensure_ascii=False)))
            db.commit()
            return dict(result, cached=False)

@app.post('/api/chat')
async def chat(body: ChatRequest):
    data = get_dashboard(body.month)
    if not data['count']:
        raise HTTPException(422, 'Сначала добавьте транзакции за выбранный месяц.')
    try:
        result = await ai_service.structured('Ответь кратко на вопрос пользователя по его финансовым агрегатам. Не выдумывай операции; если данных недостаточно, скажи об этом. Верни title и text.\n' + json.dumps({'question': body.message, 'data': data}, ensure_ascii=False), Insight)
        return {'reply': result.text, 'source': 'claude'}
    except Exception:
        raise HTTPException(503, 'Чат недоступен: проверьте ANTHROPIC_API_KEY и соединение с Claude.')
