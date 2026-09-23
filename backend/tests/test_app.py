import asyncio
import os
import tempfile
from pathlib import Path
from datetime import date
from types import SimpleNamespace
import pytest

# Отдельная БД: тесты никогда не используют пользовательские данные.
_temp = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_temp.name) / 'test.db')
os.environ.pop('ANTHROPIC_API_KEY', None)
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base, engine
from app.csv_service import parse_csv
from app.analytics import dashboard
from app.schemas import Classifications
from app import ai_service

@pytest.fixture(scope='session', autouse=True)
def close_database():
    yield
    engine.dispose()
    _temp.cleanup()

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as client:
        yield client

def test_parse_signed_and_explicit_amounts():
    rows = parse_csv('дата;описание;сумма;тип\n2026-01-01;Кофе;-1500,50;\n2026-01-02;Оклад;9000;доход\n2026-01-03;Книги;200;расход'.encode('utf-8-sig'))
    assert [r['kind'] for r in rows] == ['expense', 'income', 'expense']
    assert rows[0]['amount_minor'] == 150050

@pytest.mark.parametrize('raw', [b'', b'date,description,amount\n', b'date,description,amount\n2026-01-01,Coffee,NaN', b'date,description,amount\n2026-01-01,Coffee,1.001', b'date,description,amount\n2026-02-30,Coffee,100', b'date,description,amount\n2026-01-01,Coffee', b'date,date,amount\n2026-01-01,Coffee,10'])
def test_invalid_csv(raw):
    with pytest.raises(ValueError):
        parse_csv(raw)

def test_demo_idempotent_and_analytics(client):
    assert client.post('/api/demo').json()['imported'] == 80
    assert client.post('/api/demo').json()['imported'] == 0
    months = client.get('/api/months').json()
    assert len(months) == 2
    stats = client.get('/api/dashboard', params={'month': months[0]}).json()
    assert stats['count'] == 40
    assert len(stats['top']) == 5
    assert stats['income'] == 555000
    assert sum(c['amount'] for c in stats['categories']) == stats['expense']
    assert stats['balance'] == stats['income'] - stats['expense']
    assert stats['local_count'] == 38
    insights = client.post('/api/insights', params={'month': months[0]}).json()
    assert insights['source'] == 'local'
    assert len(insights['observations']) == 3 and len(insights['tips']) == 2
    assert client.post('/api/insights', params={'month': months[0]}).json()['cached']
    assert client.post('/api/chat', json={'month': months[0], 'message': 'Сколько на еду?'}).status_code == 503

def test_atomic_upload_and_fallback(client):
    invalid = b'date,description,amount\n2026-01-01,Coffee,-100\nwrong,Coffee,-30'
    assert client.post('/api/upload', files={'file': ('file.csv', invalid)}).status_code == 422
    assert client.get('/api/months').json() == []
    valid = b'date,description,amount\n2026-01-01,Magnum,-100\n2026-01-02,Salary,900'
    result = client.post('/api/upload', files={'file': ('file.csv', valid)})
    assert result.status_code == 200
    assert result.json()['imported'] == 2 and result.json()['warnings']
    assert client.post('/api/upload', files={'file': ('file.csv', valid)}).json()['skipped'] == 2
    assert client.get('/api/dashboard?month=2026-13').status_code == 422
    assert client.post('/api/upload', files={'file': ('file.txt', valid)}).status_code == 422

def test_closed_month_forecast_and_zero_previous():
    row = SimpleNamespace(id=1, date=date(2026, 2, 1), description='Кофе', amount_minor=280000, kind='expense', category_id=1, source='local')
    result = dashboard([row], '2026-02')
    assert result['forecast']['daily_average'] == 100
    assert result['forecast']['projected_expense'] == 2800
    assert result['forecast']['remaining'] == -2800
    assert result['change_percent'] is None

def test_batch_mapping_and_size(monkeypatch):
    calls = []
    async def mock(prompt, schema):
        import json
        batch = json.loads(prompt.split('\n', 1)[1])
        calls.append(len(batch))
        return Classifications(items=[{'id': item['id'], 'category': 'Еда'} for item in reversed(batch)])
    monkeypatch.setattr(ai_service, 'structured', mock)
    rows = [SimpleNamespace(id=i, description='Magnum', source='pending', category_id=None) for i in range(61)]
    assert asyncio.run(ai_service.categorize(rows)) == []
    assert calls == [25, 25, 11]
    assert all(r.category_id == 1 and r.source == 'claude' for r in rows)

def test_invalid_ai_ids_fallback(monkeypatch):
    async def mock(*args):
        return Classifications(items=[{'id': 999, 'category': 'Еда'}])
    monkeypatch.setattr(ai_service, 'structured', mock)
    row = SimpleNamespace(id=1, description='Аптека', source='pending', category_id=None)
    assert asyncio.run(ai_service.categorize([row]))
    assert row.source == 'local' and row.category_id == 5
