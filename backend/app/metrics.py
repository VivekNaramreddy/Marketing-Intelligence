"""Deterministic snapshot comparison. Missing observations never become zero."""
from statistics import mean


def average(values):
    present = [v for v in values if v is not None]
    return mean(present) if present else None


def analyze(rows, primary, competitors):
    selected = [r for r in rows if r['brand'] in [primary, *competitors]]
    # Latest observation per brand/platform; undated rows are fallback only.
    latest = {}
    for row in selected:
        key = (row['brand'], row['platform'])
        if key not in latest or (row['date'] or '', row['id']) > (latest[key]['date'] or '', latest[key]['id']):
            latest[key] = row
    snapshot = list(latest.values())
    own = [r for r in snapshot if r['brand'] == primary]
    platforms = []
    for row in sorted(own, key=lambda r: r['platform']):
        peers = [r for r in snapshot if r['brand'] in competitors and r['platform'] == row['platform']]
        follower_peers = [r for r in peers if r['followers'] is not None]
        rate_peers = [r for r in peers if r['engagement_rate'] is not None]
        benchmark = average([r['followers'] for r in follower_peers])
        rate = average([r['engagement_rate'] for r in rate_peers])
        platforms.append({'platform': row['platform'], 'followers': row['followers'], 'engagement_rate': row['engagement_rate'], 'competitor_average': benchmark, 'competitor_engagement_rate': rate, 'rank': 1 + sum(r['followers'] > row['followers'] for r in follower_peers) if row['followers'] is not None and follower_peers else None, 'compared_brands': len(follower_peers) + 1, 'relative_difference': (row['followers'] - benchmark) / benchmark if benchmark and row['followers'] is not None else None, 'engagement_difference': row['engagement_rate'] - rate if row['engagement_rate'] is not None and rate is not None else None, 'source_ids': [row['id'], *[r['id'] for r in peers]], 'peer_count': len(follower_peers), 'rate_peer_count': len(rate_peers), 'dates': sorted(set(r['date'] for r in [row, *peers] if r['date']))})
    rated = [p for p in platforms if p['engagement_rate'] is not None]
    ranked = [p for p in platforms if p['rank'] is not None]
    return {'audience': sum(r['followers'] for r in own if r['followers'] is not None) if any(r['followers'] is not None for r in own) else None, 'engagement_rate': average([r['engagement_rate'] for r in own]), 'best_platform': max(rated, key=lambda p: p['engagement_rate'])['platform'] if rated else None, 'leading_platforms': sum(p['rank'] == 1 for p in ranked) if ranked else None, 'ranked_platforms': len(ranked), 'platforms': platforms, 'observations': snapshot, 'coverage': {'platforms': len(own), 'follower_platforms': sum(r['followers'] is not None for r in own), 'rate_platforms': len(rated)}, 'dates': sorted(set(r['date'] for r in snapshot if r['date'])), 'methodology': 'Latest dated observation per brand/platform; latest imported row breaks ties. Undated rows are fallback. Audience sums available followers across platforms and is not unique people. Engagement is an unweighted mean of available platform rates. Benchmarks use selected competitors with available values; ranks use competition ranking (ties share rank). Different dates may be compared; inspect evidence before drawing conclusions.'}
