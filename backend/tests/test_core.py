import io
from datetime import datetime

import pandas as pd
import pytest

from app.findings import generate_findings
from app.metrics import analyze, average
from app.normalization import normalize, read_file
from app.reports import build_report


def observations(rows):
    return [dict(r, id=i) for i, r in enumerate(normalize(rows), 1)]


def test_csv_and_missing_values():
    raw = read_file('sample.csv', b'Brand,Platform,Followers,Engagement Rate\nAlpha,Instagram,"1,200",2.4%\nBeta,Instagram,900,\n')
    rows = normalize(raw)
    assert rows[0]['followers'] == 1200
    assert rows[0]['engagement_rate'] == 2.4
    assert rows[1]['engagement_rate'] is None
    assert rows[0]['views'] is None
    assert raw[0]['Followers'] == '1,200'


def test_excel():
    stream = io.BytesIO()
    pd.DataFrame([{'Brand': 'Alpha', 'Platform': 'TikTok', 'Date': datetime(2026, 9, 30), 'Followers': 981, 'Engagement Rate': None}]).to_excel(stream, index=False)
    rows = normalize(read_file('sample.xlsx', stream.getvalue()))
    assert rows[0]['followers'] == 981
    assert rows[0]['engagement_rate'] is None
    assert rows[0]['date'] == '2026-09-30'


@pytest.mark.parametrize('row', [
    {'Brand': 'Alpha', 'Followers': 10},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Followers': 'unknown'},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Followers': -1},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Followers': 'NaN'},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Followers': '1.5'},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Engagement Rate': 101},
    {'Brand': 'Alpha', 'Platform': 'Instagram', 'Followers': 3, 'Date': 'yesterday'},
    {'Brand': 'Alpha', 'Platform': 'Instagram'},
])
def test_invalid_rows(row):
    with pytest.raises(ValueError):
        normalize([row])


def test_empty_and_duplicate():
    with pytest.raises(ValueError):
        normalize([])
    row = {'brand': 'A', 'platform': 'Instagram', 'followers': 0}
    with pytest.raises(ValueError):
        normalize([row, row])
    assert normalize([row])[0]['followers'] == 0


def test_average_preserves_missing_and_zero():
    assert average([None, None]) is None
    assert average([0, 4, None]) == 2


def test_metrics_ranking_findings_and_report():
    rows = observations([
        {'brand': 'A', 'platform': 'Instagram', 'followers': 100, 'engagement_rate': 1},
        {'brand': 'B', 'platform': 'Instagram', 'followers': 200, 'engagement_rate': 3},
        {'brand': 'C', 'platform': 'Instagram', 'followers': 100, 'engagement_rate': 5},
        {'brand': 'A', 'platform': 'TikTok', 'followers': 20},
        {'brand': 'A', 'platform': 'YouTube', 'followers': 50},
        {'brand': 'B', 'platform': 'YouTube', 'followers': 10},
        {'brand': 'Unselected', 'platform': 'Instagram', 'followers': 10000, 'engagement_rate': 90},
    ])
    m = analyze(rows, 'A', ['B', 'C'])
    assert m['audience'] == 170
    assert m['engagement_rate'] == 1
    assert m['best_platform'] == 'Instagram'
    instagram = next(p for p in m['platforms'] if p['platform'] == 'Instagram')
    assert instagram['competitor_average'] == 150
    assert instagram['rank'] == 2  # ties share competition rank
    assert instagram['engagement_difference'] == -3
    assert instagram['relative_difference'] == pytest.approx(-1 / 3)
    findings = generate_findings(m)
    assert {f['type'] for f in findings} == {'Weakness', 'Strength', 'Opportunity'}
    assert all(f['source_metrics'] for f in findings)
    assert len(build_report('A', m, findings)['sections']) == 5


def test_latest_snapshot_does_not_double_count():
    rows = observations([
        {'brand': 'A', 'platform': 'Instagram', 'date': '2026-08', 'followers': 100},
        {'brand': 'A', 'platform': 'Instagram', 'date': '2026-09', 'followers': 120},
        {'brand': 'A', 'platform': 'Instagram', 'followers': 999},
    ])
    assert analyze(rows, 'A', [])['audience'] == 120
    newer_import = dict(rows[1], id=10, followers=125)
    assert analyze([*rows, newer_import], 'A', [])['audience'] == 125


def test_missing_competitors_not_zero_and_findings_bounded():
    rows = observations([{'brand': 'A', 'platform': 'Instagram', 'followers': 10}, {'brand': 'B', 'platform': 'Instagram', 'engagement_rate': 2}])
    m = analyze(rows, 'A', ['B'])
    assert m['platforms'][0]['competitor_average'] is None
    assert m['platforms'][0]['rank'] is None
    assert m['leading_platforms'] is None
    assert 'does not establish' in generate_findings(m)[0]['summary']
    assert analyze([], 'A', [])['audience'] is None
    many = analyze(observations([{'brand': 'A', 'platform': str(i), 'followers': 1} for i in range(10)]), 'A', [])
    assert len(generate_findings(many)) == 5
