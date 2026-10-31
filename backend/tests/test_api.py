import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.storage import Base, session


@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[session] = override
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()
    engine.dispose()


def test_full_demo_workflow_and_workspace_isolation(client):
    workspace = client.post('/api/workspaces', json={'name': 'Research'}).json()
    path = f'/api/workspaces/{workspace["id"]}'
    assert client.get(path + '/analysis').status_code == 422
    assert client.post(path + '/demo').json()['count'] == 21
    assert client.post(path + '/demo').status_code == 409
    result = client.get(path + '/analysis').json()
    assert result['metrics']['audience'] == 18551
    assert result['metrics']['engagement_rate'] == pytest.approx(2.215)
    assert result['metrics']['best_platform'] == 'TikTok'
    assert {f['title'] for f in result['findings']} == {'Instagram engagement gap', 'YouTube audience lead', 'Explore TikTok presence'}
    assert len(client.post(path + '/report').json()['sections']) == 5
    dataset = client.get(path + '/data').json()
    assert len(dataset['rows']) == 21
    assert client.get(path + f'/imports/{dataset["imports"][0]["id"]}').json()['rows'][0]['Followers'] == '8640'
    other = client.post('/api/workspaces', json={'name': 'Other'}).json()
    assert client.get(f'/api/workspaces/{other["id"]}/data').json()['rows'] == []
    assert client.get(f'/api/workspaces/{other["id"]}/imports/{dataset["imports"][0]["id"]}').status_code == 404
    assert client.put(path + '/selection', json={'primary_brand': 'Not imported', 'competitors': []}).status_code == 422
    assert client.put(path + '/selection', json={'primary_brand': 'Waterbury Symphony', 'competitors': ['Hartford Symphony Orchestra']}).status_code == 200
    assert client.get(path + '/analysis').json()['primary_brand'] == 'Waterbury Symphony'


def test_imports_manual_validation_and_atomicity(client):
    workspace = client.post('/api/workspaces', json={'name': 'Imports'}).json()
    path = f'/api/workspaces/{workspace["id"]}'
    assert client.post(path + '/import', files={'file': ('data.txt', b'hello')}).status_code == 422
    invalid = b'Brand,Platform,Followers\nA,Instagram,100\nB,Instagram,oops\n'
    assert client.post(path + '/import', files={'file': ('bad.csv', invalid)}).status_code == 422
    assert client.get(path + '/data').json()['rows'] == []
    assert client.post(path + '/import', files={'file': ('good.csv', b'Brand,Platform,Followers\nA,Instagram,100\n')}).status_code == 200
    stream = io.BytesIO()
    pd.DataFrame([{'Brand': 'B', 'Platform': 'Instagram', 'Followers': 120}]).to_excel(stream, index=False)
    assert client.post(path + '/import', files={'file': ('good.xlsx', stream.getvalue())}).status_code == 200
    assert client.post(path + '/manual', json={'rows': [{'brand': 'A', 'platform': 'TikTok', 'followers': 0}]}).status_code == 200
    assert len(client.get(path + '/data').json()['rows']) == 3
    assert client.post('/api/workspaces', json={'name': '  '}).status_code == 422
